import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Team, Match, TournamentState
from app.services.fixture_service import generate_round_robin_fixture
from app.services.standings_service import calculate_standings

from sqlalchemy.pool import StaticPool

# Base de datos en memoria para pruebas
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestTournamentLogic(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()
        self.client = TestClient(app)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=engine)

    def test_round_robin_even_teams(self):
        # 4 equipos: se deben generar 3 fechas de 2 partidos cada una = 6 partidos en total
        teams = [1, 2, 3, 4]
        matches = generate_round_robin_fixture(teams)
        self.assertEqual(len(matches), 6)
        rounds = set(m["round_number"] for m in matches)
        self.assertEqual(len(rounds), 3)

    def test_round_robin_odd_teams(self):
        # 3 equipos: se agregan BYEs -> 3 fechas con 1 partido normal y 1 fecha libre
        teams = [1, 2, 3]
        matches = generate_round_robin_fixture(teams)
        self.assertEqual(len(matches), 6) # 3 partidos normales + 3 partidos BYE
        byes = [m for m in matches if m["is_bye"]]
        self.assertEqual(len(byes), 3)

    def test_standings_tiebreaker_rules(self):
        # Crear 4 equipos en DB
        t1 = Team(name="Alpha FC")
        t2 = Team(name="Beta FC")
        t3 = Team(name="Gamma FC")
        t4 = Team(name="Delta FC")
        self.db.add_all([t1, t2, t3, t4])
        self.db.commit()

        # Simular Partidos
        # Fecha 1: Alpha 2 - 0 Beta, Gamma 1 - 1 Delta
        # Alpha: 3 pts (DG +2, GF 2)
        # Beta: 0 pts (DG -2, GF 0)
        # Gamma: 1 pt (DG 0, GF 1)
        # Delta: 1 pt (DG 0, GF 1)
        m1 = Match(round_number=1, home_team_id=t1.id, away_team_id=t2.id, home_score=2, away_score=0, is_completed=True, is_bye=False)
        m2 = Match(round_number=1, home_team_id=t3.id, away_team_id=t4.id, home_score=1, away_score=1, is_completed=True, is_bye=False)
        self.db.add_all([m1, m2])
        self.db.commit()

        standings = calculate_standings(self.db)
        
        # Posición 1 debe ser Alpha (3 pts)
        self.assertEqual(standings[0].team_name, "Alpha FC")
        self.assertEqual(standings[0].points, 3)

        # Posición 2 y 3 (Gamma FC vs Delta FC) empatados en Pts(1), DG(0), GF(1). Desempate alfabético: Delta FC antes que Gamma FC
        self.assertEqual(standings[1].team_name, "Delta FC")
        self.assertEqual(standings[2].team_name, "Gamma FC")

        # Posición 4 debe ser Beta (0 pts)
        self.assertEqual(standings[3].team_name, "Beta FC")

    def test_full_api_flow(self):
        admin_headers = {"X-Admin-Token": "admin-session-token-secret-2026"}

        # 0. Probar restricción de Modo Visor (debe retornar 403 Forbidden sin token)
        r_unauth = self.client.post("/api/teams", json={"name": "Equipo Hacker"})
        self.assertEqual(r_unauth.status_code, 403)

        # 1. Registrar 3 equipos como Admin
        r1 = self.client.post("/api/teams", json={"name": "Boca Juniors"}, headers=admin_headers)
        self.assertEqual(r1.status_code, 201)

        r2 = self.client.post("/api/teams", json={"name": "River Plate"}, headers=admin_headers)
        self.assertEqual(r2.status_code, 201)

        r3 = self.client.post("/api/teams", json={"name": "Independiente"}, headers=admin_headers)
        self.assertEqual(r3.status_code, 201)

        # 2. Generar Torneo como Admin
        r_gen = self.client.post("/api/tournament/generate", headers=admin_headers)
        self.assertEqual(r_gen.status_code, 200)
        status_data = r_gen.json()
        self.assertTrue(status_data["is_generated"])
        self.assertEqual(status_data["total_rounds"], 3)

        # 3. Obtener Partidos y Cargar un resultado como Admin
        r_matches = self.client.get("/api/matches")
        self.assertEqual(r_matches.status_code, 200)
        matches_tree = r_matches.json()
        
        # Buscar el primer partido no BYE
        first_match = None
        for round_item in matches_tree:
            for m in round_item["matches"]:
                if not m["is_bye"]:
                    first_match = m
                    break
            if first_match:
                break

        self.assertIsNotNone(first_match)

        # Intento de cargar marcador sin token (debe fallar 403)
        r_score_unauth = self.client.put(f"/api/matches/{first_match['id']}/score", json={"home_score": 3, "away_score": 1})
        self.assertEqual(r_score_unauth.status_code, 403)

        # Cargar marcador 3 - 1 con token de Admin
        r_score = self.client.put(f"/api/matches/{first_match['id']}/score", json={"home_score": 3, "away_score": 1}, headers=admin_headers)
        self.assertEqual(r_score.status_code, 200)
        self.assertTrue(r_score.json()["is_completed"])

        # 4. Verificar Tabla de Posiciones (Disponible para Visor sin token)
        r_standings = self.client.get("/api/standings")
        self.assertEqual(r_standings.status_code, 200)
        standings = r_standings.json()
        self.assertEqual(len(standings), 3)
        self.assertEqual(standings[0]["points"], 3)
        self.assertEqual(standings[0]["goal_difference"], 2)

        # 5. Probar eliminación de un equipo como Admin
        team_to_delete_id = r3.json()["id"]
        r_del = self.client.delete(f"/api/teams/{team_to_delete_id}", headers=admin_headers)
        self.assertEqual(r_del.status_code, 204)

        # Verificar que queden 2 equipos
        r_teams = self.client.get("/api/teams")
        self.assertEqual(len(r_teams.json()), 2)

    def test_upload_shield_limits(self):
        admin_headers = {"X-Admin-Token": "admin-session-token-secret-2026"}
        
        # 1. Probar subida de imagen válida (pequeño SVG/PNG)
        valid_file = ("shield.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01", "image/png")
        r_upload = self.client.post("/api/teams/upload-shield", files={"file": valid_file}, headers=admin_headers)
        self.assertEqual(r_upload.status_code, 200)
        self.assertTrue("url" in r_upload.json())

        # 2. Probar subida de archivo que excede 5 MB
        large_content = b"0" * (6 * 1024 * 1024)  # 6 MB
        large_file = ("huge_shield.png", large_content, "image/png")
        r_huge = self.client.post("/api/teams/upload-shield", files={"file": large_file}, headers=admin_headers)
        self.assertEqual(r_huge.status_code, 400)
        self.assertIn("supera el límite", r_huge.json()["detail"])

if __name__ == "__main__":
    unittest.main()

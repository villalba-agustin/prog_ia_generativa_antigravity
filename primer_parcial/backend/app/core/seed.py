import asyncio
from datetime import date, timedelta
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.tournament import Tournament
from app.models.team import Team
from app.models.player import Player
from app.models.user import User
from app.models.pitch import Pitch
from app.models.match import Match
from app.models.round import Round
from app.services.fixture_engine import FixtureEngine
from app.services.match_service import MatchService
from app.schemas.match import MatchResultUpdate
from app.schemas.stats import MatchStatCreate
from sqlalchemy import select


async def run_seed():
    print("Iniciando carga de datos demo realistas...")
    async with AsyncSessionLocal() as db:
        # 1. Asegurar Canchas 1 a 4
        for i in range(1, 5):
            p_q = await db.execute(select(Pitch).where(Pitch.pitch_number == i))
            if not p_q.scalar_one_or_none():
                db.add(Pitch(id=i, name=f"Cancha {i}", pitch_number=i, is_available=True))
        await db.commit()

        # 2. Administrador general
        admin_q = await db.execute(select(User).where(User.email == "admin@ligabarrios.com"))
        if not admin_q.scalar_one_or_none():
            db.add(User(
                email="admin@ligabarrios.com",
                hashed_password=get_password_hash("admin1234"),
                role="ADMINISTRADOR",
                is_active=True
            ))
        await db.commit()

        # 3. Torneo Activo
        tourn_q = await db.execute(select(Tournament).where(Tournament.is_active == True))
        tournament = tourn_q.scalar_one_or_none()
        if not tournament:
            tournament = Tournament(
                name="Torneo Apertura 2026 - Liga de Barrios y Fincas",
                start_date=date.today() - timedelta(days=14),
                is_active=True,
                fixture_generated=False
            )
            db.add(tournament)
            await db.commit()
            await db.refresh(tournament)

        # 4. Equipos
        teams_data = [
            {"name": "Barrio San Martín", "short_name": "BSM", "delegate": "Carlos Gomez", "phone": "381-4552101", "email": "delegado.bsm@ligabarrios.com"},
            {"name": "Finca Los Álamos", "short_name": "FLA", "delegate": "Roberto Díaz", "phone": "381-4552102", "email": "delegado.fla@ligabarrios.com"},
            {"name": "Deportivo La Rinconada", "short_name": "DLR", "delegate": "Marcos Paz", "phone": "381-4552103", "email": "delegado.dlr@ligabarrios.com"},
            {"name": "Los Naranjos FC", "short_name": "LN", "delegate": "Jorge Soler", "phone": "381-4552104", "email": "delegado.ln@ligabarrios.com"},
            {"name": "Atlético Villa Unión", "short_name": "AVU", "delegate": "Esteban Morales", "phone": "381-4552105", "email": "delegado.avu@ligabarrios.com"},
            {"name": "Finca Santa Anita", "short_name": "FSA", "delegate": "Ignacio Rivas", "phone": "381-4552106", "email": "delegado.fsa@ligabarrios.com"},
            {"name": "La Amistad del Centro", "short_name": "LAC", "delegate": "Daniel Albarracín", "phone": "381-4552107", "email": "delegado.lac@ligabarrios.com"},
            {"name": "Esperanza Norte", "short_name": "EN", "delegate": "Fernando Cruz", "phone": "381-4552108", "email": "delegado.en@ligabarrios.com"},
        ]

        created_teams = []
        for t_info in teams_data:
            t_q = await db.execute(select(Team).where(Team.tournament_id == tournament.id, Team.short_name == t_info["short_name"]))
            team = t_q.scalar_one_or_none()
            if not team:
                team = Team(
                    tournament_id=tournament.id,
                    name=t_info["name"],
                    short_name=t_info["short_name"],
                    logo_url=None,
                    delegate_name=t_info["delegate"],
                    delegate_phone=t_info["phone"],
                    is_active=True
                )
                db.add(team)
                await db.flush()

                # Crear usuario delegado
                u_q = await db.execute(select(User).where(User.email == t_info["email"]))
                if not u_q.scalar_one_or_none():
                    db.add(User(
                        email=t_info["email"],
                        hashed_password=get_password_hash("delegado1234"),
                        role="DELEGADO",
                        team_id=team.id,
                        is_active=True
                    ))

            created_teams.append(team)
        await db.commit()

        # 5. Jugadores para cada equipo (planteles de 7 a 9 jugadores)
        names_pool = [
            ("Lucas", "González"), ("Mateo", "Rodríguez"), ("Joaquín", "Fernández"),
            ("Agustín", "López"), ("Lautaro", "Martínez"), ("Nicolás", "Pérez"),
            ("Facundo", "Gómez"), ("Franco", "Romero"), ("Bautista", "Sánchez")
        ]

        dni_counter = 40100000
        for t_idx, team in enumerate(created_teams):
            pl_q = await db.execute(select(Player).where(Player.team_id == team.id))
            if not pl_q.scalars().all():
                for j_num, (fn, ln) in enumerate(names_pool, start=1):
                    dni_counter += 1
                    player = Player(
                        team_id=team.id,
                        first_name=f"{fn} {team.short_name}",
                        last_name=ln,
                        dni=str(dni_counter),
                        birth_date=date(1995 + (j_num % 10), (j_num % 12) + 1, (j_num % 28) + 1),
                        jersey_number=j_num,
                        is_enabled=True
                    )
                    db.add(player)
        await db.commit()

        # 6. Generar Fixture si no está generado
        if not tournament.fixture_generated:
            print("Generando fixture automático con 4 canchas y slots de 70 min...")
            await FixtureEngine.generate_fixture_for_tournament(tournament.id, db)
            print("Fixture generado con éxito.")

        # 7. Cargar resultados demo en las primeras dos fechas
        rounds_q = await db.execute(
            select(Round).where(Round.tournament_id == tournament.id).order_by(Round.round_number)
        )
        rounds = list(rounds_q.scalars().all())

        # Fecha 1: Cargar resultados
        if len(rounds) >= 1:
            r1_matches_q = await db.execute(select(Match).where(Match.round_id == rounds[0].id))
            r1_matches = list(r1_matches_q.scalars().all())
            demo_scores_r1 = [(3, 1), (2, 2), (1, 0), (0, 2)]
            for m_idx, match in enumerate(r1_matches):
                if match.status == "PENDIENTE" and m_idx < len(demo_scores_r1):
                    h_score, a_score = demo_scores_r1[m_idx]
                    await MatchService.record_result(
                        match.id,
                        MatchResultUpdate(home_score=h_score, away_score=a_score),
                        db
                    )
                    # Cargar estadísticas de jugadores (goles y tarjetas)
                    h_players = (await db.execute(select(Player).where(Player.team_id == match.home_team_id))).scalars().all()
                    a_players = (await db.execute(select(Player).where(Player.team_id == match.away_team_id))).scalars().all()
                    
                    stats_payload = []
                    if h_players and h_score > 0:
                        stats_payload.append(MatchStatCreate(
                            player_id=h_players[0].id,
                            team_id=match.home_team_id,
                            goals=h_score,
                            yellow_cards=1,
                            red_cards=0
                        ))
                    if a_players and a_score > 0:
                        stats_payload.append(MatchStatCreate(
                            player_id=a_players[0].id,
                            team_id=match.away_team_id,
                            goals=a_score,
                            yellow_cards=0,
                            red_cards=0
                        ))
                    if h_players and len(h_players) > 1:
                        stats_payload.append(MatchStatCreate(
                            player_id=h_players[1].id,
                            team_id=match.home_team_id,
                            goals=0,
                            yellow_cards=1,
                            red_cards=0
                        ))
                    if stats_payload:
                        await MatchService.record_player_stats(match.id, stats_payload, db)

        # Fecha 2: Cargar resultados
        if len(rounds) >= 2:
            r2_matches_q = await db.execute(select(Match).where(Match.round_id == rounds[1].id))
            r2_matches = list(r2_matches_q.scalars().all())
            demo_scores_r2 = [(2, 1), (0, 0), (3, 2), (1, 4)]
            for m_idx, match in enumerate(r2_matches):
                if match.status == "PENDIENTE" and m_idx < len(demo_scores_r2):
                    h_score, a_score = demo_scores_r2[m_idx]
                    await MatchService.record_result(
                        match.id,
                        MatchResultUpdate(home_score=h_score, away_score=a_score),
                        db
                    )
                    h_players = (await db.execute(select(Player).where(Player.team_id == match.home_team_id))).scalars().all()
                    a_players = (await db.execute(select(Player).where(Player.team_id == match.away_team_id))).scalars().all()
                    stats_payload = []
                    if h_players and h_score > 0:
                        stats_payload.append(MatchStatCreate(
                            player_id=h_players[0].id,
                            team_id=match.home_team_id,
                            goals=h_score,
                            yellow_cards=0,
                            red_cards=0
                        ))
                    if a_players and a_score > 0:
                        stats_payload.append(MatchStatCreate(
                            player_id=a_players[0].id,
                            team_id=match.away_team_id,
                            goals=a_score,
                            yellow_cards=1,
                            red_cards=0
                        ))
                    if stats_payload:
                        await MatchService.record_player_stats(match.id, stats_payload, db)

        print("¡Datos demo cargados con éxito!")


if __name__ == "__main__":
    asyncio.run(run_seed())

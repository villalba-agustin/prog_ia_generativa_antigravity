import httpx

BASE_URL = "http://127.0.0.1:8000"

def run_e2e_verification():
    print("=== Iniciando Verificación End-to-End del Servidor ===")
    
    # 1. Registrar 4 Equipos
    teams_to_add = [
        {"name": "Boca Juniors", "shield_url": "https://upload.wikimedia.org/wikipedia/commons/4/41/Logotipo_del_Club_Atl%C3%A9tico_Boca_Juniors.svg"},
        {"name": "River Plate", "shield_url": "https://upload.wikimedia.org/wikipedia/commons/a/ac/Escudo_del_C_A_River_Plate.svg"},
        {"name": "Independiente", "shield_url": "https://upload.wikimedia.org/wikipedia/commons/d/db/Escudo_de_Club_Atl%C3%A9tico_Independiente.svg"},
        {"name": "Racing Club", "shield_url": "https://upload.wikimedia.org/wikipedia/commons/5/56/Escudo_de_Racing_Club.svg"}
    ]

    admin_headers = {"X-Admin-Token": "admin-session-token-secret-2026"}

    for team in teams_to_add:
        resp = httpx.post(f"{BASE_URL}/api/teams", json=team, headers=admin_headers)
        if resp.status_code == 201:
            print(f"[OK] Equipo creado: {team['name']}")
        else:
            print(f"[INFO] {resp.json().get('detail')}")

    # 2. Generar Torneo
    resp_gen = httpx.post(f"{BASE_URL}/api/tournament/generate", headers=admin_headers)
    print(f"[OK] Torneo Generado: {resp_gen.json()}")

    # 3. Obtener Partidos de la Fecha 1
    resp_matches = httpx.get(f"{BASE_URL}/api/matches/round/1")
    matches = resp_matches.json()
    print(f"[OK] Partidos Fecha 1 ({len(matches)} partidos):")

    for idx, match in enumerate(matches, start=1):
        if not match["is_bye"]:
            h_name = match["home_team"]["name"]
            a_name = match["away_team"]["name"]
            print(f"   Partido {idx}: {h_name} vs {a_name}")
            
            # Cargar resultado para el primer partido (2-1) y el segundo (1-1)
            score_h = 2 if idx == 1 else 1
            score_a = 1 if idx == 1 else 1
            
            resp_score = httpx.put(f"{BASE_URL}/api/matches/{match['id']}/score", json={
                "home_score": score_h,
                "away_score": score_a
            }, headers=admin_headers)
            print(f"   -> Marcador guardado: {h_name} {score_h} - {score_a} {a_name}")

    # 4. Consultar Tabla de Posiciones
    resp_standings = httpx.get(f"{BASE_URL}/api/standings")
    standings = resp_standings.json()
    
    print("\n=== TABLA DE POSICIONES ACTUALIZADA ===")
    print(f"{'POS':<4} {'EQUIPO':<18} {'PJ':<4} {'PG':<4} {'PE':<4} {'PP':<4} {'GF':<4} {'GC':<4} {'DG':<4} {'PTS':<4}")
    print("-" * 65)
    for row in standings:
        print(f"{row['position']:<4} {row['team_name']:<18} {row['played']:<4} {row['won']:<4} {row['drawn']:<4} {row['lost']:<4} {row['goals_for']:<4} {row['goals_against']:<4} {row['goal_difference']:<4} {row['points']:<4}")

if __name__ == "__main__":
    run_e2e_verification()

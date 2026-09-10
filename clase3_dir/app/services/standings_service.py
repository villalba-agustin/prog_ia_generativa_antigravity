from typing import List, Dict, Any
from functools import cmp_to_key
from sqlalchemy.orm import Session
from app.models import Team, Match
from app.schemas import StandingRow

def calculate_standings(db: Session) -> List[StandingRow]:
    teams = db.query(Team).all()
    if not teams:
        return []

    # Diccionario inicial de estadísticas por equipo
    stats = {}
    for team in teams:
        stats[team.id] = {
            "team_id": team.id,
            "team_name": team.name,
            "shield_url": team.shield_url,
            "played": 0,
            "won": 0,
            "drawn": 0,
            "lost": 0,
            "goals_for": 0,
            "goals_against": 0,
            "goal_difference": 0,
            "points": 0
        }

    # Obtener partidos completados (no byes)
    completed_matches = db.query(Match).filter(
        Match.is_completed == True,
        Match.is_bye == False
    ).all()

    # Mapa de resultados de enfrentamientos directos: (team1_id, team2_id) -> puntos obtenidos por team1 contra team2
    # Guardaremos una estructura de enfrentamientos directos
    direct_matches: Dict[tuple, Dict[str, int]] = {}

    for match in completed_matches:
        h_id = match.home_team_id
        a_id = match.away_team_id
        h_score = match.home_score
        a_score = match.away_score

        if h_id not in stats or a_id not in stats:
            continue

        # Actualizar PJ
        stats[h_id]["played"] += 1
        stats[a_id]["played"] += 1

        # Goles
        stats[h_id]["goals_for"] += h_score
        stats[h_id]["goals_against"] += a_score
        stats[a_id]["goals_for"] += a_score
        stats[a_id]["goals_against"] += h_score

        # Puntos y Resultados
        if h_score > a_score:
            stats[h_id]["won"] += 1
            stats[h_id]["points"] += 3
            stats[a_id]["lost"] += 1
            
            # Direct match tracker
            direct_matches[(h_id, a_id)] = {"pts": 3, "gf": h_score, "ga": a_score}
            direct_matches[(a_id, h_id)] = {"pts": 0, "gf": a_score, "ga": h_score}
        elif a_score > h_score:
            stats[a_id]["won"] += 1
            stats[a_id]["points"] += 3
            stats[h_id]["lost"] += 1
            
            # Direct match tracker
            direct_matches[(a_id, h_id)] = {"pts": 3, "gf": a_score, "ga": h_score}
            direct_matches[(h_id, a_id)] = {"pts": 0, "gf": h_score, "ga": a_score}
        else:
            stats[h_id]["drawn"] += 1
            stats[h_id]["points"] += 1
            stats[a_id]["drawn"] += 1
            stats[a_id]["points"] += 1

            # Direct match tracker
            direct_matches[(h_id, a_id)] = {"pts": 1, "gf": h_score, "ga": a_score}
            direct_matches[(a_id, h_id)] = {"pts": 1, "gf": a_score, "ga": h_score}

    # Calcular Diferencia de Goles
    for t_id in stats:
        stats[t_id]["goal_difference"] = stats[t_id]["goals_for"] - stats[t_id]["goals_against"]

    stats_list = list(stats.values())

    # Función comparadora con los 4 criterios de desempate + Nombre
    def compare_teams(a: Dict[str, Any], b: Dict[str, Any]) -> int:
        # 1° Mayor cantidad de puntos
        if a["points"] != b["points"]:
            return -1 if a["points"] > b["points"] else 1

        # 2° Mayor diferencia de gol (DG)
        if a["goal_difference"] != b["goal_difference"]:
            return -1 if a["goal_difference"] > b["goal_difference"] else 1

        # 3° Mayor cantidad de goles a favor (GF)
        if a["goals_for"] != b["goals_for"]:
            return -1 if a["goals_for"] > b["goals_for"] else 1

        # 4° Resultado entre sí (Head-to-head)
        h2h_ab = direct_matches.get((a["team_id"], b["team_id"]))
        h2h_ba = direct_matches.get((b["team_id"], a["team_id"]))
        if h2h_ab and h2h_ba:
            if h2h_ab["pts"] != h2h_ba["pts"]:
                return -1 if h2h_ab["pts"] > h2h_ba["pts"] else 1
            # Si empataron en puntos de enfrentamiento directo, comparar DG directa
            dg_ab = h2h_ab["gf"] - h2h_ab["ga"]
            dg_ba = h2h_ba["gf"] - h2h_ba["ga"]
            if dg_ab != dg_ba:
                return -1 if dg_ab > dg_ba else 1

        # 5° Nombre alfabético (A -> Z)
        name_a = a["team_name"].lower()
        name_b = b["team_name"].lower()
        if name_a != name_b:
            return -1 if name_a < name_b else 1

        return 0

    sorted_stats = sorted(stats_list, key=cmp_to_key(compare_teams))

    # Formatear la respuesta con la posición (1-based)
    standing_rows = []
    for idx, item in enumerate(sorted_stats, start=1):
        standing_rows.append(StandingRow(
            position=idx,
            team_id=item["team_id"],
            team_name=item["team_name"],
            shield_url=item["shield_url"],
            played=item["played"],
            won=item["won"],
            drawn=item["drawn"],
            lost=item["lost"],
            goals_for=item["goals_for"],
            goals_against=item["goals_against"],
            goal_difference=item["goal_difference"],
            points=item["points"]
        ))

    return standing_rows

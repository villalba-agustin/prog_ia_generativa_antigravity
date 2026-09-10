from typing import List, Dict, Any

def generate_round_robin_fixture(team_ids: List[int]) -> List[Dict[str, Any]]:
    """
    Genera la lista de partidos para un torneo Round Robin (todos contra todos 1 sola vez).
    Si el número de equipos es impar, agrega un BYE (fecha libre).
    Retorna una lista de diccionarios con:
    [
      {
        "round_number": int,
        "home_team_id": int or None,
        "away_team_id": int or None,
        "is_bye": bool
      }, ...
    ]
    """
    teams = list(team_ids)
    if len(teams) < 2:
        raise ValueError("Se requieren al menos 2 equipos para generar un torneo.")

    # Si es impar, agregamos None para representar el equipo libre
    if len(teams) % 2 != 0:
        teams.append(None)

    num_teams = len(teams)
    num_rounds = num_teams - 1
    half = num_teams // 2

    matches = []

    for round_idx in range(num_rounds):
        round_number = round_idx + 1
        
        for i in range(half):
            t1 = teams[i]
            t2 = teams[num_teams - 1 - i]

            if t1 is None or t2 is None:
                # Partido de fecha libre
                active_team = t1 if t1 is not None else t2
                matches.append({
                    "round_number": round_number,
                    "home_team_id": active_team,
                    "away_team_id": None,
                    "is_bye": True
                })
            else:
                # Alternamos localía para un fixture más equilibrado
                if (round_idx + i) % 2 == 0:
                    home, away = t1, t2
                else:
                    home, away = t2, t1

                matches.append({
                    "round_number": round_number,
                    "home_team_id": home,
                    "away_team_id": away,
                    "is_bye": False
                })

        # Rotar elementos manteniendo teams[0] fijo
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]

    return matches

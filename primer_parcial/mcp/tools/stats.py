"""
Tools: get_top_scorers, get_card_statistics
Scoring and disciplinary statistics for Liga de Barrios y Fincas.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy import text
from db import get_db_connection

async def get_top_scorers(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Devuelve la lista de máximos goleadores del torneo activo.
    
    Args:
        limit: Cantidad máxima de goleadores a retornar (por defecto 10).
    """
    if limit < 1:
        limit = 10
    if limit > 100:
        limit = 100

    async with get_db_connection() as conn:
        query = text("""
            SELECT 
                p.id as player_id,
                p.first_name || ' ' || p.last_name as player_name,
                p.jersey_number,
                t.name as team_name,
                t.short_name as team_short_name,
                SUM(ms.goals) as total_goals,
                COUNT(DISTINCT ms.match_id) as matches_with_stats
            FROM match_stats ms
            JOIN players p ON ms.player_id = p.id
            JOIN teams t ON ms.team_id = t.id
            JOIN tournaments tour ON t.tournament_id = tour.id
            WHERE tour.is_active = TRUE
            GROUP BY p.id, p.first_name, p.last_name, p.jersey_number, t.name, t.short_name
            HAVING SUM(ms.goals) > 0
            ORDER BY total_goals DESC, player_name ASC
            LIMIT :limit;
        """)
        res = await conn.execute(query, {"limit": limit})
        rows = res.fetchall()

        scorers = []
        for rank, r in enumerate(rows, start=1):
            scorers.append({
                "rank": rank,
                "player_id": str(r.player_id),
                "player_name": r.player_name,
                "jersey_number": r.jersey_number,
                "team_name": r.team_name,
                "team_short_name": r.team_short_name,
                "goals": int(r.total_goals),
                "matches_played": int(r.matches_with_stats)
            })
        return scorers

async def get_card_statistics(group_by: str = "team") -> Dict[str, Any]:
    """
    Devuelve estadísticas de tarjetas amarillas y rojas del torneo activo.
    
    Args:
        group_by: Criterio de agrupación. Opciones permitidas: 'team' (por equipo), 'player' (por jugador), o 'all' (ambas).
    """
    valid_groupings = ["team", "player", "all"]
    clean_group = group_by.lower().strip()
    if clean_group not in valid_groupings:
        return {
            "error": f"group_by inválido: '{group_by}'. Opciones permitidas: {valid_groupings}"
        }

    results: Dict[str, Any] = {
        "group_by": clean_group,
        "cards_by_team": [],
        "cards_by_player": []
    }

    async with get_db_connection() as conn:
        if clean_group in ["team", "all"]:
            team_query = text("""
                SELECT 
                    t.id as team_id,
                    t.name as team_name,
                    t.short_name,
                    COALESCE(SUM(ms.yellow_cards), 0) as total_yellows,
                    COALESCE(SUM(ms.red_cards), 0) as total_reds,
                    COALESCE(SUM(ms.yellow_cards * 1 + ms.red_cards * 3), 0) as fair_play_points_deducted
                FROM teams t
                JOIN tournaments tour ON t.tournament_id = tour.id
                LEFT JOIN match_stats ms ON ms.team_id = t.id
                WHERE tour.is_active = TRUE
                GROUP BY t.id, t.name, t.short_name
                ORDER BY total_reds DESC, total_yellows DESC, t.name ASC;
            """)
            res = await conn.execute(team_query)
            for r in res.fetchall():
                results["cards_by_team"].append({
                    "team_id": str(r.team_id),
                    "team_name": r.team_name,
                    "short_name": r.short_name,
                    "yellow_cards": int(r.total_yellows),
                    "red_cards": int(r.total_reds),
                    "fair_play_penalty_points": int(r.fair_play_points_deducted)
                })

        if clean_group in ["player", "all"]:
            player_query = text("""
                SELECT 
                    p.id as player_id,
                    p.first_name || ' ' || p.last_name as player_name,
                    p.jersey_number,
                    t.name as team_name,
                    SUM(ms.yellow_cards) as total_yellows,
                    SUM(ms.red_cards) as total_reds
                FROM match_stats ms
                JOIN players p ON ms.player_id = p.id
                JOIN teams t ON ms.team_id = t.id
                JOIN tournaments tour ON t.tournament_id = tour.id
                WHERE tour.is_active = TRUE
                GROUP BY p.id, p.first_name, p.last_name, p.jersey_number, t.name
                HAVING (SUM(ms.yellow_cards) > 0 OR SUM(ms.red_cards) > 0)
                ORDER BY total_reds DESC, total_yellows DESC, player_name ASC;
            """)
            res = await conn.execute(player_query)
            for r in res.fetchall():
                results["cards_by_player"].append({
                    "player_id": str(r.player_id),
                    "player_name": r.player_name,
                    "jersey_number": r.jersey_number,
                    "team_name": r.team_name,
                    "yellow_cards": int(r.total_yellows),
                    "red_cards": int(r.total_reds)
                })

        # Remove empty keys if single group
        if clean_group == "team":
            del results["cards_by_player"]
        elif clean_group == "player":
            del results["cards_by_team"]

        return results

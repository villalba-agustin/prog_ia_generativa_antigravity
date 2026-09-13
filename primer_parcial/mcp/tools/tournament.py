"""
Tools: get_tournament_summary, get_standings
Tournament overview and official standings table for Liga de Barrios y Fincas.
"""

from typing import Dict, Any, List
from sqlalchemy import text
from db import get_db_connection

async def get_tournament_summary() -> Dict[str, Any]:
    """
    Devuelve un resumen completo del torneo activo:
    - Cantidad de equipos
    - Cantidad de jugadores
    - Cantidad de fechas (rounds)
    - Cantidad total de partidos
    - Partidos jugados
    - Partidos pendientes
    - Partidos suspendidos
    - Partidos cancelados
    """
    async with get_db_connection() as conn:
        # Get active tournament
        t_res = await conn.execute(text("""
            SELECT id, name, is_active, fixture_generated, start_date
            FROM tournaments
            WHERE is_active = TRUE
            LIMIT 1;
        """))
        tourney = t_res.fetchone()

        if not tourney:
            return {
                "status": "no_active_tournament",
                "message": "No hay ningún torneo activo actualmente."
            }

        tourney_id = tourney.id

        # Total teams
        teams_count_res = await conn.execute(
            text("SELECT COUNT(*) FROM teams WHERE tournament_id = :tid;"),
            {"tid": tourney_id}
        )
        total_teams = teams_count_res.scalar() or 0

        # Total players
        players_count_res = await conn.execute(
            text("""
                SELECT COUNT(p.id) 
                FROM players p 
                JOIN teams t ON p.team_id = t.id 
                WHERE t.tournament_id = :tid;
            """),
            {"tid": tourney_id}
        )
        total_players = players_count_res.scalar() or 0

        # Total rounds
        rounds_count_res = await conn.execute(
            text("SELECT COUNT(*) FROM rounds WHERE tournament_id = :tid;"),
            {"tid": tourney_id}
        )
        total_rounds = rounds_count_res.scalar() or 0

        # Matches breakdown by status
        matches_res = await conn.execute(
            text("""
                SELECT 
                    COUNT(*) as total_matches,
                    COUNT(*) FILTER (WHERE status = 'JUGADO') as played,
                    COUNT(*) FILTER (WHERE status = 'PENDIENTE') as pending,
                    COUNT(*) FILTER (WHERE status = 'SUSPENDIDO') as suspended,
                    COUNT(*) FILTER (WHERE status = 'CANCELADO') as cancelled
                FROM matches
                WHERE tournament_id = :tid;
            """),
            {"tid": tourney_id}
        )
        m_stats = matches_res.fetchone()

        return {
            "tournament": {
                "id": str(tourney.id),
                "name": tourney.name,
                "is_active": tourney.is_active,
                "fixture_generated": tourney.fixture_generated,
                "start_date": tourney.start_date.isoformat() if tourney.start_date else None
            },
            "summary": {
                "total_teams": total_teams,
                "total_players": total_players,
                "total_rounds": total_rounds,
                "total_matches": m_stats.total_matches if m_stats else 0,
                "matches_played": m_stats.played if m_stats else 0,
                "matches_pending": m_stats.pending if m_stats else 0,
                "matches_suspended": m_stats.suspended if m_stats else 0,
                "matches_cancelled": m_stats.cancelled if m_stats else 0
            }
        }

async def get_standings() -> List[Dict[str, Any]]:
    """
    Devuelve la tabla actual de posiciones oficial de la Liga de Barrios y Fincas.
    Incluye:
    - equipo: nombre del equipo
    - PJ: partidos jugados
    - PG: partidos ganados
    - PE: partidos empatados
    - PP: partidos perdidos
    - GF: goles a favor
    - GC: goles en contra
    - DG: diferencia de gol
    - PTS: puntos obtenidos
    - fair_play_score: puntaje de conducta fair play
    - position: posición en la tabla
    """
    async with get_db_connection() as conn:
        query = text("""
            SELECT 
                s.position,
                t.name AS team_name,
                t.short_name,
                s.played AS "PJ",
                s.won AS "PG",
                s.drawn AS "PE",
                s.lost AS "PP",
                s.goals_for AS "GF",
                s.goals_against AS "GC",
                s.goal_diff AS "DG",
                s.points AS "PTS",
                s.fair_play_score
            FROM standings s
            JOIN teams t ON s.team_id = t.id
            JOIN tournaments tour ON s.tournament_id = tour.id
            WHERE tour.is_active = TRUE
            ORDER BY s.position ASC, s.points DESC, s.goal_diff DESC, s.goals_for DESC;
        """)
        res = await conn.execute(query)
        rows = res.fetchall()

        standings = []
        for r in rows:
            standings.append({
                "position": r.position,
                "team": r.team_name,
                "short_name": r.short_name,
                "PJ": r.PJ,
                "PG": r.PG,
                "PE": r.PE,
                "PP": r.PP,
                "GF": r.GF,
                "GC": r.GC,
                "DG": r.DG,
                "PTS": r.PTS,
                "fair_play_score": r.fair_play_score
            })
        return standings

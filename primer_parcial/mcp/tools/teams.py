"""
Tools: list_teams, list_players
Read-only queries for teams and players in Liga de Barrios y Fincas.
"""

from typing import List, Dict, Any, Optional
import uuid
from sqlalchemy import text
from db import get_db_connection

async def list_teams(include_inactive: bool = False) -> List[Dict[str, Any]]:
    """
    Devuelve los equipos registrados en el torneo activo.
    
    Args:
        include_inactive: Si es True, incluye equipos marcados como no activos.
    """
    async with get_db_connection() as conn:
        filter_clause = "" if include_inactive else "WHERE t.is_active = TRUE"
        query = text(f"""
            SELECT 
                t.id,
                t.name,
                t.short_name,
                t.delegate_name,
                t.delegate_phone,
                t.is_active,
                t.created_at,
                COUNT(p.id) as player_count
            FROM teams t
            LEFT JOIN players p ON p.team_id = t.id
            {filter_clause}
            GROUP BY t.id, t.name, t.short_name, t.delegate_name, t.delegate_phone, t.is_active, t.created_at
            ORDER BY t.name ASC;
        """)
        res = await conn.execute(query)
        rows = res.fetchall()

        teams = []
        for r in rows:
            teams.append({
                "id": str(r.id),
                "name": r.name,
                "short_name": r.short_name,
                "delegate_name": r.delegate_name,
                "delegate_phone": r.delegate_phone,
                "is_active": r.is_active,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "player_count": int(r.player_count)
            })
        return teams

async def list_players(
    team_id: Optional[str] = None,
    team_name: Optional[str] = None,
    only_enabled: bool = True
) -> List[Dict[str, Any]]:
    """
    Devuelve los jugadores registrados y el equipo al que pertenecen.
    
    Args:
        team_id: UUID opcional del equipo para filtrar.
        team_name: Nombre o subcadena opcional del equipo para filtrar.
        only_enabled: Si es True, solo devuelve jugadores habilitados.
    """
    conditions = ["1=1"]
    params: Dict[str, Any] = {}

    if team_id:
        try:
            # Validate UUID format
            valid_uuid = str(uuid.UUID(team_id))
            conditions.append("p.team_id = :team_id")
            params["team_id"] = valid_uuid
        except ValueError:
            return [{"error": f"Formato de team_id inválido: '{team_id}'. Debe ser un UUID."}]

    if team_name:
        conditions.append("LOWER(t.name) LIKE LOWER(:team_name)")
        params["team_name"] = f"%{team_name.strip()}%"

    if only_enabled:
        conditions.append("p.is_enabled = TRUE")

    where_str = " AND ".join(conditions)

    async with get_db_connection() as conn:
        query = text(f"""
            SELECT 
                p.id,
                p.first_name,
                p.last_name,
                p.dni,
                p.jersey_number,
                p.birth_date,
                p.is_enabled,
                t.id as team_id,
                t.name as team_name,
                t.short_name as team_short_name
            FROM players p
            JOIN teams t ON p.team_id = t.id
            WHERE {where_str}
            ORDER BY t.name ASC, p.jersey_number ASC;
        """)
        res = await conn.execute(query, params)
        rows = res.fetchall()

        players = []
        for r in rows:
            players.append({
                "id": str(r.id),
                "full_name": f"{r.first_name} {r.last_name}",
                "first_name": r.first_name,
                "last_name": r.last_name,
                "dni": r.dni,
                "jersey_number": r.jersey_number,
                "birth_date": r.birth_date.isoformat() if r.birth_date else None,
                "is_enabled": r.is_enabled,
                "team_id": str(r.team_id),
                "team_name": r.team_name,
                "team_short_name": r.team_short_name
            })
        return players

import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.tournament import Tournament
from app.models.standings import Standing
from app.models.user import User
from app.schemas.standings import StandingResponse
from app.api.deps import require_admin
from app.services.standings_engine import StandingsEngine

router = APIRouter()


@router.get("/", response_model=List[StandingResponse])
async def get_standings(
    tournament_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Obtener la tabla de posiciones oficial ordenada según el reglamento"""
    if not tournament_id:
        active_t = await db.execute(select(Tournament.id).where(Tournament.is_active == True))
        active_id = active_t.scalar_one_or_none()
        if not active_id:
            return []
        tournament_id = active_id

    query = await db.execute(
        select(Standing)
        .options(selectinload(Standing.team))
        .where(Standing.tournament_id == tournament_id)
        .order_by(Standing.position)
    )
    standings = query.scalars().all()

    return [
        StandingResponse(
            id=s.id,
            tournament_id=s.tournament_id,
            team_id=s.team_id,
            team_name=s.team.name if s.team else "Equipo Desconocido",
            team_short_name=s.team.short_name if s.team else "EQ",
            team_logo_url=s.team.logo_url if s.team else None,
            played=s.played,
            won=s.won,
            drawn=s.drawn,
            lost=s.lost,
            goals_for=s.goals_for,
            goals_against=s.goals_against,
            goal_diff=s.goal_diff,
            points=s.points,
            fair_play_score=s.fair_play_score,
            position=s.position
        )
        for s in standings
    ]


@router.post("/recalculate", response_model=List[StandingResponse])
async def force_recalculate_standings(
    tournament_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> Any:
    """Forzar recálculo de la tabla de posiciones con todos los criterios de desempate"""
    if not tournament_id:
        active_t = await db.execute(select(Tournament.id).where(Tournament.is_active == True))
        active_id = active_t.scalar_one_or_none()
        if not active_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No hay torneo activo")
        tournament_id = active_id

    await StandingsEngine.recalculate_tournament_standings(tournament_id, db)
    return await get_standings(tournament_id=tournament_id, db=db)

import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.match import Match
from app.models.user import User
from app.schemas.match import MatchResponse, MatchResultUpdate, MatchStatusUpdate, MatchRescheduleRequest
from app.api.deps import require_admin
from app.services.match_service import MatchService
from app.services.reschedule_engine import RescheduleEngine

router = APIRouter()


@router.get("/", response_model=List[MatchResponse])
async def list_matches(
    round_id: Optional[uuid.UUID] = None,
    tournament_id: Optional[uuid.UUID] = None,
    team_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Listar partidos con filtros opcionales (por fecha, equipo o estado)"""
    stmt = (
        select(Match)
        .options(
            selectinload(Match.home_team),
            selectinload(Match.away_team),
            selectinload(Match.pitch)
        )
    )
    if round_id:
        stmt = stmt.where(Match.round_id == round_id)
    if tournament_id:
        stmt = stmt.where(Match.tournament_id == tournament_id)
    if team_id:
        stmt = stmt.where((Match.home_team_id == team_id) | (Match.away_team_id == team_id))
    if status_filter:
        stmt = stmt.where(Match.status == status_filter.upper())

    stmt = stmt.order_by(Match.match_date, Match.start_time, Match.pitch_id)
    query = await db.execute(stmt)
    return query.scalars().all()


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(match_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Any:
    """Obtener detalle de un partido"""
    stmt = (
        select(Match)
        .options(
            selectinload(Match.home_team),
            selectinload(Match.away_team),
            selectinload(Match.pitch)
        )
        .where(Match.id == match_id)
    )
    query = await db.execute(stmt)
    match = query.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partido no encontrado")
    return match


@router.post("/{match_id}/result", response_model=MatchResponse)
async def record_match_result(
    match_id: uuid.UUID,
    result_in: MatchResultUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> Any:
    """
    Cargar el resultado de un partido (solo Administrador).
    REGLA DE NEGOCIO: Una vez cargado el resultado, NO debe poder modificarse desde la aplicación.
    Al pasar a JUGADO, se recalculan automáticamente las estadísticas y la tabla.
    """
    match = await MatchService.record_result(match_id, result_in, db)

    # Recargar con relaciones
    stmt = (
        select(Match)
        .options(
            selectinload(Match.home_team),
            selectinload(Match.away_team),
            selectinload(Match.pitch)
        )
        .where(Match.id == match.id)
    )
    query = await db.execute(stmt)
    return query.scalar_one()


@router.post("/{match_id}/status", response_model=MatchResponse)
async def update_match_status(
    match_id: uuid.UUID,
    status_in: MatchStatusUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> Any:
    """Suspender o cancelar un partido no jugado"""
    match = await MatchService.update_status(match_id, status_in, db)
    stmt = (
        select(Match)
        .options(
            selectinload(Match.home_team),
            selectinload(Match.away_team),
            selectinload(Match.pitch)
        )
        .where(Match.id == match.id)
    )
    query = await db.execute(stmt)
    return query.scalar_one()


@router.post("/{match_id}/reschedule", response_model=MatchResponse)
async def reschedule_match(
    match_id: uuid.UUID,
    reschedule_in: Optional[MatchRescheduleRequest] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> Any:
    """
    Reprogramar automáticamente un partido suspendido o cancelado.
    Busca el primer slot (cancha + horario) disponible sin solapamientos.
    """
    target_d = reschedule_in.target_date if reschedule_in else None
    match = await RescheduleEngine.reschedule_match(match_id, db, preferred_start_date=target_d)

    stmt = (
        select(Match)
        .options(
            selectinload(Match.home_team),
            selectinload(Match.away_team),
            selectinload(Match.pitch)
        )
        .where(Match.id == match.id)
    )
    query = await db.execute(stmt)
    return query.scalar_one()

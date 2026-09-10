import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.tournament import Tournament
from app.models.user import User
from app.schemas.tournament import TournamentCreate, TournamentResponse
from app.schemas.match import RoundResponse
from app.api.deps import require_admin
from app.services.fixture_engine import FixtureEngine

router = APIRouter()


@router.get("/active", response_model=TournamentResponse)
async def get_active_tournament(db: AsyncSession = Depends(get_db)) -> Any:
    """Obtener el torneo activo actualmente"""
    query = await db.execute(select(Tournament).where(Tournament.is_active == True))
    tournament = query.scalar_one_or_none()
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No hay ningún torneo activo actualmente")
    return tournament


@router.get("/", response_model=List[TournamentResponse])
async def list_tournaments(db: AsyncSession = Depends(get_db)) -> Any:
    """Listar todos los torneos registrados"""
    query = await db.execute(select(Tournament).order_by(Tournament.created_at.desc()))
    return query.scalars().all()


@router.post("/", response_model=TournamentResponse)
async def create_tournament(
    tourn_in: TournamentCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> Any:
    """Crear un nuevo torneo (solo Administrador). Si se crea como activo, valida unicidad."""
    if tourn_in.is_active:
        active_check = await db.execute(select(Tournament).where(Tournament.is_active == True))
        if active_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un torneo activo en el sistema. Desactiva el actual antes de activar uno nuevo."
            )

    tournament = Tournament(
        name=tourn_in.name,
        start_date=tourn_in.start_date,
        is_active=tourn_in.is_active,
        fixture_generated=False
    )
    db.add(tournament)
    await db.commit()
    await db.refresh(tournament)
    return tournament


@router.post("/{tournament_id}/generate-fixture", response_model=List[RoundResponse])
async def generate_fixture(
    tournament_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> Any:
    """
    Generar el fixture automáticamente para el torneo.
    - Todos contra todos una sola rueda
    - 4 canchas, slots de 70 min entre 11:00 y 18:00
    - Ningún equipo 2 veces en la misma fecha
    - Bloqueo de fixture una vez generado
    """
    rounds = await FixtureEngine.generate_fixture_for_tournament(tournament_id, db)
    return rounds

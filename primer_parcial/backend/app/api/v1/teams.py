import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.tournament import Tournament
from app.models.team import Team
from app.models.player import Player
from app.models.user import User
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse
from app.schemas.player import PlayerResponse
from app.api.deps import require_admin, require_delegate_or_admin

router = APIRouter()


@router.get("/", response_model=List[TeamResponse])
async def list_teams(
    tournament_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Listar equipos (del torneo activo por defecto o del ID solicitado)"""
    if not tournament_id:
        active_t = await db.execute(select(Tournament.id).where(Tournament.is_active == True))
        active_id = active_t.scalar_one_or_none()
        if not active_id:
            return []
        tournament_id = active_id

    query = await db.execute(
        select(Team, func.count(Player.id).label("players_count"))
        .outerjoin(Player, Team.id == Player.team_id)
        .where(Team.tournament_id == tournament_id)
        .group_by(Team.id)
        .order_by(Team.name)
    )
    results = []
    for team, count in query.all():
        team_dict = TeamResponse.model_validate(team)
        team_dict.players_count = count
        results.append(team_dict)
    return results


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(team_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Any:
    """Obtener detalle de un equipo"""
    query = await db.execute(
        select(Team, func.count(Player.id).label("players_count"))
        .outerjoin(Player, Team.id == Player.team_id)
        .where(Team.id == team_id)
        .group_by(Team.id)
    )
    row = query.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipo no encontrado")
    team, count = row
    res = TeamResponse.model_validate(team)
    res.players_count = count
    return res


@router.get("/{team_id}/players", response_model=List[PlayerResponse])
async def get_team_players(team_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Any:
    """Obtener plantel de jugadores de un equipo"""
    query = await db.execute(
        select(Player).where(Player.team_id == team_id).order_by(Player.jersey_number)
    )
    return query.scalars().all()


@router.post("/", response_model=TeamResponse)
async def create_team(
    team_in: TeamCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> Any:
    """Crear un nuevo equipo (solo Administrador). Valida que no haya duplicados."""
    target_tourn_id = team_in.tournament_id
    if not target_tourn_id:
        active_t = await db.execute(select(Tournament.id).where(Tournament.is_active == True))
        target_tourn_id = active_t.scalar_one_or_none()
        if not target_tourn_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No hay torneo activo para asociar el equipo")

    # Validar que el torneo no tenga fixture generado
    t_query = await db.execute(select(Tournament).where(Tournament.id == target_tourn_id))
    tourn = t_query.scalar_one_or_none()
    if tourn and tourn.fixture_generated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pueden agregar equipos a un torneo cuyo fixture ya fue generado")

    # Validar nombre único
    dup_query = await db.execute(
        select(Team).where(
            Team.tournament_id == target_tourn_id,
            (func.lower(Team.name) == team_in.name.strip().lower()) |
            (func.lower(Team.short_name) == team_in.short_name.strip().lower())
        )
    )
    if dup_query.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya existe un equipo con ese nombre o nombre corto en este torneo")

    team = Team(
        tournament_id=target_tourn_id,
        name=team_in.name.strip(),
        short_name=team_in.short_name.strip().upper(),
        logo_url=team_in.logo_url,
        delegate_name=team_in.delegate_name.strip(),
        delegate_phone=team_in.delegate_phone.strip(),
        is_active=team_in.is_active
    )
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: uuid.UUID,
    team_in: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_delegate_or_admin)
) -> Any:
    """Actualizar datos de equipo (Admin, o Delegado sobre su propio equipo)"""
    query = await db.execute(select(Team).where(Team.id == team_id))
    team = query.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipo no encontrado")

    if current_user.role == "DELEGADO" and current_user.team_id != team_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Un delegado solo puede modificar datos de su propio equipo")

    if team_in.name is not None and team_in.name != team.name:
        if current_user.role == "DELEGADO":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Los delegados no pueden cambiar el nombre oficial del equipo")
        team.name = team_in.name.strip()

    if team_in.short_name is not None and team_in.short_name != team.short_name:
        if current_user.role == "DELEGADO":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Los delegados no pueden cambiar el nombre corto del equipo")
        team.short_name = team_in.short_name.strip().upper()

    if team_in.logo_url is not None:
        team.logo_url = team_in.logo_url
    if team_in.delegate_name is not None:
        team.delegate_name = team_in.delegate_name.strip()
    if team_in.delegate_phone is not None:
        team.delegate_phone = team_in.delegate_phone.strip()
    if team_in.is_active is not None and current_user.role == "ADMINISTRADOR":
        team.is_active = team_in.is_active

    await db.commit()
    await db.refresh(team)
    return team

import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.player import Player
from app.models.team import Team
from app.models.user import User
from app.schemas.player import PlayerCreate, PlayerUpdate, PlayerResponse
from app.api.deps import require_admin, require_delegate_or_admin

router = APIRouter()


@router.get("/", response_model=List[PlayerResponse])
async def list_players(
    team_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Listar jugadores (opcionalmente filtrados por equipo)"""
    stmt = select(Player)
    if team_id:
        stmt = stmt.where(Player.team_id == team_id)
    stmt = stmt.order_by(Player.last_name, Player.first_name)
    query = await db.execute(stmt)
    return query.scalars().all()


@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(player_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Any:
    """Obtener detalle de un jugador"""
    query = await db.execute(select(Player).where(Player.id == player_id))
    player = query.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jugador no encontrado")
    return player


@router.post("/", response_model=PlayerResponse)
async def create_player(
    player_in: PlayerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_delegate_or_admin)
) -> Any:
    """
    Registrar un nuevo jugador.
    - El delegado solo puede inscribir en su propio equipo.
    - DNI único en el torneo.
    - Camiseta única dentro del equipo.
    """
    if current_user.role == "DELEGADO" and current_user.team_id != player_in.team_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Un delegado solo puede inscribir jugadores en su propio equipo"
        )

    # Validar existencia del equipo
    team_query = await db.execute(select(Team).where(Team.id == player_in.team_id))
    team = team_query.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipo no encontrado")

    # Validar DNI único
    dni_clean = player_in.dni.strip()
    dni_query = await db.execute(select(Player).where(Player.dni == dni_clean))
    if dni_query.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un jugador registrado con el DNI {dni_clean}"
        )

    # Validar camiseta única en el equipo
    jersey_query = await db.execute(
        select(Player).where(
            Player.team_id == player_in.team_id,
            Player.jersey_number == player_in.jersey_number
        )
    )
    if jersey_query.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La camiseta número {player_in.jersey_number} ya está asignada a otro jugador de este equipo"
        )

    player = Player(
        team_id=player_in.team_id,
        first_name=player_in.first_name.strip(),
        last_name=player_in.last_name.strip(),
        dni=dni_clean,
        birth_date=player_in.birth_date,
        jersey_number=player_in.jersey_number,
        is_enabled=player_in.is_enabled
    )
    db.add(player)
    await db.commit()
    await db.refresh(player)
    return player


@router.put("/{player_id}", response_model=PlayerResponse)
async def update_player(
    player_id: uuid.UUID,
    player_in: PlayerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_delegate_or_admin)
) -> Any:
    """Actualizar datos de un jugador (Admin o Delegado)"""
    query = await db.execute(select(Player).where(Player.id == player_id))
    player = query.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jugador no encontrado")

    if current_user.role == "DELEGADO" and current_user.team_id != player.team_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para modificar jugadores de otro equipo")

    if player_in.first_name is not None:
        player.first_name = player_in.first_name.strip()
    if player_in.last_name is not None:
        player.last_name = player_in.last_name.strip()
    if player_in.birth_date is not None:
        player.birth_date = player_in.birth_date

    # Si cambia DNI, verificar unicidad
    if player_in.dni is not None and player_in.dni.strip() != player.dni:
        new_dni = player_in.dni.strip()
        dup_dni = await db.execute(select(Player).where(Player.dni == new_dni, Player.id != player_id))
        if dup_dni.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El DNI ya se encuentra registrado")
        player.dni = new_dni

    # Si cambia camiseta, verificar unicidad en equipo
    if player_in.jersey_number is not None and player_in.jersey_number != player.jersey_number:
        dup_jersey = await db.execute(
            select(Player).where(
                Player.team_id == player.team_id,
                Player.jersey_number == player_in.jersey_number,
                Player.id != player_id
            )
        )
        if dup_jersey.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"La camiseta {player_in.jersey_number} ya está en uso en el equipo")
        player.jersey_number = player_in.jersey_number

    # Solo el admin puede modificar habilitación
    if player_in.is_enabled is not None:
        if current_user.role != "ADMINISTRADOR":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo los administradores pueden modificar la habilitación de un jugador")
        player.is_enabled = player_in.is_enabled

    await db.commit()
    await db.refresh(player)
    return player


@router.patch("/{player_id}/toggle-enable", response_model=PlayerResponse)
async def toggle_player_enabled(
    player_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> Any:
    """Habilitar o deshabilitar un jugador (solo Administrador)"""
    query = await db.execute(select(Player).where(Player.id == player_id))
    player = query.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jugador no encontrado")

    player.is_enabled = not player.is_enabled
    await db.commit()
    await db.refresh(player)
    return player

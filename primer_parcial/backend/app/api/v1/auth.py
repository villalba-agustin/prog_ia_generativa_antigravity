from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.user import User
from app.models.team import Team
from app.schemas.auth import Token, LoginRequest, UserCreate, UserResponse
from app.api.deps import get_current_user, require_admin

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Autenticación de usuario con email y contraseña (JSON)"""
    query = await db.execute(select(User).where(User.email == login_data.email))
    user = query.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo")

    access_token = create_access_token(
        subject=user.id,
        role=user.role,
        team_id=user.team_id
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "email": user.email,
        "team_id": user.team_id
    }


@router.post("/login/form", response_model=Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Endpoint compatible con OAuth2PasswordRequestForm para Swagger UI"""
    query = await db.execute(select(User).where(User.email == form_data.username))
    user = query.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        subject=user.id,
        role=user.role,
        team_id=user.team_id
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "email": user.email,
        "team_id": user.team_id
    }


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Obtener datos del usuario autenticado actual"""
    return current_user


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin)
) -> Any:
    """Crear un nuevo usuario (solo Administrador)"""
    existing = await db.execute(select(User).where(User.email == user_in.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El email ya está registrado")

    if user_in.role == "DELEGADO" and not user_in.team_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Un delegado debe tener un equipo asignado")

    if user_in.team_id:
        team_check = await db.execute(select(Team).where(Team.id == user_in.team_id))
        if not team_check.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipo no encontrado")

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role.upper(),
        team_id=user_in.team_id,
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

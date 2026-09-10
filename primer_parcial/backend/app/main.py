from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.pitch import Pitch
from app.models.user import User
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Inicializar datos mínimos indispensables (Canchas 1 a 4 y Admin inicial)
    async with AsyncSessionLocal() as session:
        # 1. Asegurar las 4 canchas reglamentarias
        for i in range(1, 5):
            query = await session.execute(select(Pitch).where(Pitch.pitch_number == i))
            if not query.scalar_one_or_none():
                session.add(Pitch(id=i, name=f"Cancha {i}", pitch_number=i, is_available=True))

        # 2. Asegurar usuario Administrador inicial
        admin_query = await session.execute(
            select(User).where(User.email == settings.INITIAL_ADMIN_EMAIL)
        )
        if not admin_query.scalar_one_or_none():
            admin_user = User(
                email=settings.INITIAL_ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.INITIAL_ADMIN_PASSWORD),
                role="ADMINISTRADOR",
                team_id=None,
                is_active=True
            )
            session.add(admin_user)

        await session.commit()

    yield
    # Shutdown logic if needed


app = FastAPI(
    title="Liga de Barrios y Fincas - API",
    description="Sistema integral de administración para torneo amateur de fútbol.",
    version="1.0.0",
    lifespan=lifespan
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT
    }


app.include_router(api_router, prefix="/api/v1")

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import engine, Base
from app.routers import teams, tournament, matches, auth

# Crear tablas en SQLite si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Torneo de Fútbol API",
    description="Sistema de gestión de torneos de fútbol en Python con FastAPI y SQLite",
    version="1.0.0"
)

# Incluir Routers de API
app.include_router(teams.router)
app.include_router(tournament.router)
app.include_router(matches.router)
app.include_router(auth.router)

# Ruta del directorio estático
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

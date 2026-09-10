import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Team, Match, TournamentState
from app.schemas import TeamCreate, TeamUpdate, TeamResponse
from app.routers.auth import require_admin

router = APIRouter(prefix="/api/teams", tags=["Equipos"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif", ".ico", ".bmp"}

@router.get("", response_model=List[TeamResponse])
def get_teams(db: Session = Depends(get_db)):
    return db.query(Team).order_by(Team.name.asc()).all()

@router.post("/upload-shield", dependencies=[Depends(require_admin)])
async def upload_shield(file: UploadFile = File(...)):
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    
    is_valid_type = (file.content_type and file.content_type.startswith("image/")) or (ext in ALLOWED_EXTENSIONS)
    if not is_valid_type:
        raise HTTPException(
            status_code=400,
            detail="Formato de archivo no soportado. Solo se permiten imágenes (PNG, JPG, SVG, WEBP, GIF)."
        )

    if not ext or ext not in ALLOWED_EXTENSIONS:
        ext = ".png"

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        actual_mb = len(content) / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"La imagen supera el límite de tamaño permitido (5 MB). Tamaño actual: {actual_mb:.2f} MB."
        )

    new_filename = f"shield_{uuid.uuid4().hex[:10]}{ext}"
    filepath = os.path.join(UPLOAD_DIR, new_filename)

    with open(filepath, "wb") as f:
        f.write(content)

    return {"url": f"/static/uploads/{new_filename}"}

@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_team(team_in: TeamCreate, db: Session = Depends(get_db)):
    state = db.query(TournamentState).first()
    if state and state.is_generated:
        raise HTTPException(
            status_code=400,
            detail="No se pueden agregar equipos una vez que el torneo ya ha sido generado."
        )

    existing = db.query(Team).filter(Team.name.ilike(team_in.name.strip())).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un equipo registrado con el nombre '{team_in.name}'."
        )

    new_team = Team(
        name=team_in.name.strip(),
        shield_url=team_in.shield_url.strip() if team_in.shield_url else None
    )
    db.add(new_team)
    db.commit()
    db.refresh(new_team)
    return new_team

@router.put("/{team_id:int}", response_model=TeamResponse, dependencies=[Depends(require_admin)])
def update_team(team_id: int, team_in: TeamUpdate, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado.")

    if team_in.name and team_in.name.strip() != team.name:
        existing = db.query(Team).filter(Team.name.ilike(team_in.name.strip()), Team.id != team_id).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Ya existe otro equipo con el nombre '{team_in.name}'.")
        team.name = team_in.name.strip()

    if team_in.shield_url is not None:
        team.shield_url = team_in.shield_url.strip() if team_in.shield_url else None

    db.commit()
    db.refresh(team)
    return team

@router.delete("/{team_id:int}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado.")

    state = db.query(TournamentState).first()
    if state and state.is_generated:
        state.is_generated = False
        state.total_rounds = 0
        db.query(Match).delete()

    db.delete(team)
    db.commit()
    return None

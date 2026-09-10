from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Team, Match, TournamentState
from app.schemas import TournamentStatusResponse
from app.services.fixture_service import generate_round_robin_fixture
from app.routers.auth import require_admin

router = APIRouter(prefix="/api/tournament", tags=["Torneo"])

@router.get("/status", response_model=TournamentStatusResponse)
def get_tournament_status(db: Session = Depends(get_db)):
    state = db.query(TournamentState).first()
    if not state:
        state = TournamentState(id=1, is_generated=False, total_rounds=0)
        db.add(state)
        db.commit()
        db.refresh(state)

    total_teams = db.query(Team).count()
    return TournamentStatusResponse(
        is_generated=state.is_generated,
        name=state.name,
        total_rounds=state.total_rounds,
        total_teams=total_teams
    )

@router.post("/generate", response_model=TournamentStatusResponse, dependencies=[Depends(require_admin)])
def generate_tournament(db: Session = Depends(get_db)):
    state = db.query(TournamentState).first()
    if not state:
        state = TournamentState(id=1, is_generated=False, total_rounds=0)
        db.add(state)

    teams = db.query(Team).all()
    if len(teams) < 2:
        raise HTTPException(
            status_code=400,
            detail="Se necesitan al menos 2 equipos para poder generar el torneo."
        )

    # Si ya fue generado, limpiar partidos anteriores
    db.query(Match).delete()

    team_ids = [t.id for t in teams]
    fixture_matches = generate_round_robin_fixture(team_ids)

    max_round = 0
    for match_data in fixture_matches:
        match_obj = Match(
            round_number=match_data["round_number"],
            home_team_id=match_data["home_team_id"],
            away_team_id=match_data["away_team_id"],
            is_completed=False,
            is_bye=match_data["is_bye"]
        )
        db.add(match_obj)
        if match_data["round_number"] > max_round:
            max_round = match_data["round_number"]

    state.is_generated = True
    state.total_rounds = max_round
    db.commit()
    db.refresh(state)

    return TournamentStatusResponse(
        is_generated=state.is_generated,
        name=state.name,
        total_rounds=state.total_rounds,
        total_teams=len(teams)
    )

@router.post("/reset", response_model=TournamentStatusResponse, dependencies=[Depends(require_admin)])
def reset_tournament(db: Session = Depends(get_db)):
    state = db.query(TournamentState).first()
    if state:
        state.is_generated = False
        state.total_rounds = 0

    db.query(Match).delete()
    db.commit()

    total_teams = db.query(Team).count()
    return TournamentStatusResponse(
        is_generated=False,
        name=state.name if state else "Torneo de Fútbol 2026",
        total_rounds=0,
        total_teams=total_teams
    )

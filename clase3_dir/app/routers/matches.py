from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Match
from app.schemas import MatchResponse, RoundMatches, MatchScoreUpdate, StandingRow
from app.services.standings_service import calculate_standings
from app.routers.auth import require_admin

router = APIRouter(prefix="/api", tags=["Partidos y Posiciones"])

@router.get("/matches", response_model=List[RoundMatches])
def get_all_matches(db: Session = Depends(get_db)):
    matches = db.query(Match).order_by(Match.round_number.asc(), Match.id.asc()).all()
    
    rounds_map = {}
    for m in matches:
        r_num = m.round_number
        if r_num not in rounds_map:
            rounds_map[r_num] = []
        rounds_map[r_num].append(m)

    result = []
    for r_num in sorted(rounds_map.keys()):
        result.append(RoundMatches(
            round_number=r_num,
            matches=[MatchResponse.model_validate(m) for m in rounds_map[r_num]]
        ))
    return result

@router.get("/matches/round/{round_number}", response_model=List[MatchResponse])
def get_matches_by_round(round_number: int, db: Session = Depends(get_db)):
    matches = db.query(Match).filter(Match.round_number == round_number).order_by(Match.id.asc()).all()
    return matches

@router.put("/matches/{match_id}/score", response_model=MatchResponse, dependencies=[Depends(require_admin)])
def update_match_score(match_id: int, score_in: MatchScoreUpdate, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Partido no encontrado.")

    if match.is_bye:
        raise HTTPException(status_code=400, detail="No se pueden asignar goles a una fecha libre (BYE).")

    match.home_score = score_in.home_score
    match.away_score = score_in.away_score
    match.is_completed = True
    db.commit()
    db.refresh(match)
    return match

@router.delete("/matches/{match_id}/score", response_model=MatchResponse, dependencies=[Depends(require_admin)])
def clear_match_score(match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Partido no encontrado.")

    match.home_score = None
    match.away_score = None
    match.is_completed = False
    db.commit()
    db.refresh(match)
    return match

@router.get("/standings", response_model=List[StandingRow])
def get_standings(db: Session = Depends(get_db)):
    return calculate_standings(db)

import uuid
from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PitchResponse(BaseModel):
    id: int
    name: str
    pitch_number: int
    is_available: bool

    class Config:
        from_attributes = True


class RoundResponse(BaseModel):
    id: uuid.UUID
    tournament_id: uuid.UUID
    round_number: int
    name: str
    scheduled_date: date
    status: str

    class Config:
        from_attributes = True


class MatchTeamSummary(BaseModel):
    id: uuid.UUID
    name: str
    short_name: str
    logo_url: Optional[str] = None

    class Config:
        from_attributes = True


class MatchResponse(BaseModel):
    id: uuid.UUID
    round_id: uuid.UUID
    tournament_id: uuid.UUID
    home_team_id: uuid.UUID
    away_team_id: uuid.UUID
    pitch_id: int
    match_date: date
    start_time: time
    end_time: time
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: str  # PENDIENTE, JUGADO, SUSPENDIDO, CANCELADO
    is_locked: bool
    played_at: Optional[datetime] = None

    home_team: Optional[MatchTeamSummary] = None
    away_team: Optional[MatchTeamSummary] = None
    pitch: Optional[PitchResponse] = None

    class Config:
        from_attributes = True


class MatchResultUpdate(BaseModel):
    home_score: int = Field(..., ge=0, description="Goles equipo local (no negativo)")
    away_score: int = Field(..., ge=0, description="Goles equipo visitante (no negativo)")


class MatchStatusUpdate(BaseModel):
    status: str = Field(..., description="Nuevo estado: SUSPENDIDO o CANCELADO")


class MatchRescheduleRequest(BaseModel):
    target_date: Optional[date] = None

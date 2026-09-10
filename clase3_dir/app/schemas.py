from pydantic import BaseModel, Field
from typing import Optional, List

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Nombre del equipo")
    shield_url: Optional[str] = Field(None, description="URL del escudo o icono del equipo")

class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Nombre del equipo")
    shield_url: Optional[str] = Field(None, description="URL del escudo o icono del equipo")

class TeamResponse(BaseModel):
    id: int
    name: str
    shield_url: Optional[str] = None

    class Config:
        from_attributes = True

class MatchScoreUpdate(BaseModel):
    home_score: int = Field(..., ge=0, description="Goles marcados por el equipo local")
    away_score: int = Field(..., ge=0, description="Goles marcados por el equipo visitante")

class MatchResponse(BaseModel):
    id: int
    round_number: int
    home_team: Optional[TeamResponse] = None
    away_team: Optional[TeamResponse] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    is_completed: bool
    is_bye: bool

    class Config:
        from_attributes = True

class RoundMatches(BaseModel):
    round_number: int
    matches: List[MatchResponse]

class StandingRow(BaseModel):
    position: int
    team_id: int
    team_name: str
    shield_url: Optional[str] = None
    played: int          # PJ
    won: int             # PG
    drawn: int           # PE
    lost: int            # PP
    goals_for: int       # GF
    goals_against: int   # GC
    goal_difference: int # DG
    points: int          # Pts

class TournamentStatusResponse(BaseModel):
    is_generated: bool
    name: str
    total_rounds: int
    total_teams: int

class AdminLoginRequest(BaseModel):
    password: str

class AdminLoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    message: str

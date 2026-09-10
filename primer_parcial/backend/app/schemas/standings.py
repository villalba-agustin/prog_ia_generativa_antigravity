import uuid
from typing import Optional
from pydantic import BaseModel


class StandingResponse(BaseModel):
    id: uuid.UUID
    tournament_id: uuid.UUID
    team_id: uuid.UUID
    team_name: str
    team_short_name: str
    team_logo_url: Optional[str] = None
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_diff: int
    points: int
    fair_play_score: int
    position: int

    class Config:
        from_attributes = True

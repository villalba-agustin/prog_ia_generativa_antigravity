import uuid
from typing import Optional, List
from pydantic import BaseModel, Field


class MatchStatCreate(BaseModel):
    player_id: uuid.UUID
    team_id: uuid.UUID
    goals: int = Field(0, ge=0)
    yellow_cards: int = Field(0, ge=0, le=2)
    red_cards: int = Field(0, ge=0, le=1)


class MatchStatBulkCreate(BaseModel):
    stats: List[MatchStatCreate]


class MatchStatResponse(BaseModel):
    id: uuid.UUID
    match_id: uuid.UUID
    team_id: uuid.UUID
    player_id: uuid.UUID
    goals: int
    yellow_cards: int
    red_cards: int

    class Config:
        from_attributes = True


class TopScorerResponse(BaseModel):
    player_id: uuid.UUID
    player_name: str
    team_name: str
    jersey_number: int
    goals: int


class FairPlayResponse(BaseModel):
    team_id: uuid.UUID
    team_name: str
    yellow_cards: int
    red_cards: int
    fair_play_score: int

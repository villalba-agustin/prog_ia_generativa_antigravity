import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class TeamBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    short_name: str = Field(..., min_length=2, max_length=10)
    logo_url: Optional[str] = None
    delegate_name: str = Field(..., min_length=2, max_length=100)
    delegate_phone: str = Field(..., min_length=6, max_length=50)
    is_active: bool = True


class TeamCreate(TeamBase):
    tournament_id: Optional[uuid.UUID] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    short_name: Optional[str] = Field(None, min_length=2, max_length=10)
    logo_url: Optional[str] = None
    delegate_name: Optional[str] = Field(None, min_length=2, max_length=100)
    delegate_phone: Optional[str] = Field(None, min_length=6, max_length=50)
    is_active: Optional[bool] = None


class TeamResponse(TeamBase):
    id: uuid.UUID
    tournament_id: uuid.UUID
    created_at: datetime
    players_count: Optional[int] = 0

    class Config:
        from_attributes = True

import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class PlayerBase(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    dni: str = Field(..., min_length=6, max_length=20)
    birth_date: date
    jersey_number: int = Field(..., ge=1, le=99)
    is_enabled: bool = True


class PlayerCreate(PlayerBase):
    team_id: uuid.UUID


class PlayerUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    dni: Optional[str] = Field(None, min_length=6, max_length=20)
    birth_date: Optional[date] = None
    jersey_number: Optional[int] = Field(None, ge=1, le=99)
    is_enabled: Optional[bool] = None


class PlayerResponse(PlayerBase):
    id: uuid.UUID
    team_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

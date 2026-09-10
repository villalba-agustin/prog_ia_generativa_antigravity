import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class TournamentBase(BaseModel):
    name: str
    start_date: date
    is_active: bool = True


class TournamentCreate(TournamentBase):
    pass


class TournamentUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    is_active: Optional[bool] = None


class TournamentResponse(TournamentBase):
    id: uuid.UUID
    fixture_generated: bool
    created_at: datetime

    class Config:
        from_attributes = True

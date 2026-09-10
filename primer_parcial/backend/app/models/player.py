import uuid
from datetime import date
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.team import Team
    from app.models.stats import MatchStat


class Player(BaseModel):
    __tablename__ = "players"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dni: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    jersey_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    team: Mapped["Team"] = relationship("Team", back_populates="players")
    match_stats: Mapped[List["MatchStat"]] = relationship("MatchStat", back_populates="player", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("team_id", "jersey_number", name="uq_team_jersey_number"),
    )

import uuid
from datetime import date
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.tournament import Tournament
    from app.models.match import Match


class Round(BaseModel):
    __tablename__ = "rounds"

    tournament_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False
    )
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDIENTE", nullable=False)

    # Relationships
    tournament: Mapped["Tournament"] = relationship("Tournament", back_populates="rounds")
    matches: Mapped[List["Match"]] = relationship("Match", back_populates="round", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tournament_id", "round_number", name="uq_round_number_per_tournament"),
    )

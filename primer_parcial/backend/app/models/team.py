import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.tournament import Tournament
    from app.models.player import Player
    from app.models.user import User
    from app.models.standings import Standing


class Team(BaseModel):
    __tablename__ = "teams"

    tournament_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    short_name: Mapped[str] = mapped_column(String(10), nullable=False)
    logo_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    delegate_name: Mapped[str] = mapped_column(String(100), nullable=False)
    delegate_phone: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    tournament: Mapped["Tournament"] = relationship("Tournament", back_populates="teams")
    players: Mapped[List["Player"]] = relationship("Player", back_populates="team", cascade="all, delete-orphan")
    users: Mapped[List["User"]] = relationship("User", back_populates="team")
    standing: Mapped[Optional["Standing"]] = relationship("Standing", back_populates="team", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tournament_id", "name", name="uq_team_name_per_tournament"),
        UniqueConstraint("tournament_id", "short_name", name="uq_team_short_name_per_tournament"),
    )

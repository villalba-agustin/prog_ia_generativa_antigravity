import uuid
from datetime import date, time, datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, Date, Time, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.round import Round
    from app.models.team import Team
    from app.models.pitch import Pitch
    from app.models.stats import MatchStat


class Match(BaseModel):
    __tablename__ = "matches"

    round_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rounds.id", ondelete="CASCADE"),
        nullable=False
    )
    tournament_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False
    )
    home_team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="RESTRICT"),
        nullable=False
    )
    away_team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="RESTRICT"),
        nullable=False
    )
    pitch_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pitches.id", ondelete="RESTRICT"),
        nullable=False
    )
    match_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    home_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    away_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDIENTE", nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    played_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    round: Mapped["Round"] = relationship("Round", back_populates="matches")
    home_team: Mapped["Team"] = relationship("Team", foreign_keys=[home_team_id])
    away_team: Mapped["Team"] = relationship("Team", foreign_keys=[away_team_id])
    pitch: Mapped["Pitch"] = relationship("Pitch", back_populates="matches")
    stats: Mapped[List["MatchStat"]] = relationship("MatchStat", back_populates="match", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("home_team_id <> away_team_id", name="chk_different_match_teams"),
        CheckConstraint("home_score IS NULL OR home_score >= 0", name="chk_valid_home_score"),
        CheckConstraint("away_score IS NULL OR away_score >= 0", name="chk_valid_away_score"),
        Index("idx_match_pitch_date_time", "pitch_id", "match_date", "start_time"),
        Index("idx_match_round", "round_id"),
    )

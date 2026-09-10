import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Integer, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.match import Match
    from app.models.team import Team
    from app.models.player import Player


class MatchStat(BaseModel):
    __tablename__ = "match_stats"

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False
    )
    goals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    yellow_cards: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    red_cards: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    match: Mapped["Match"] = relationship("Match", back_populates="stats")
    team: Mapped["Team"] = relationship("Team")
    player: Mapped["Player"] = relationship("Player", back_populates="match_stats")

    __table_args__ = (
        UniqueConstraint("match_id", "player_id", name="uq_player_match_stats"),
        CheckConstraint("goals >= 0", name="chk_valid_player_goals"),
        CheckConstraint("yellow_cards >= 0 AND yellow_cards <= 2", name="chk_valid_yellow_cards"),
        CheckConstraint("red_cards >= 0 AND red_cards <= 1", name="chk_valid_red_cards"),
    )

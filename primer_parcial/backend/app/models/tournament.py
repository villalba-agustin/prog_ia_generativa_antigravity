from datetime import date
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, Date, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.team import Team
    from app.models.round import Round
    from app.models.standings import Standing


class Tournament(BaseModel):
    __tablename__ = "tournaments"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fixture_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Relationships
    teams: Mapped[List["Team"]] = relationship("Team", back_populates="tournament", cascade="all, delete-orphan")
    rounds: Mapped[List["Round"]] = relationship("Round", back_populates="tournament", cascade="all, delete-orphan")
    standings: Mapped[List["Standing"]] = relationship("Standing", back_populates="tournament", cascade="all, delete-orphan")

    __table_args__ = (
        # PostgreSQL partial unique index: exactly 1 active tournament at any time
        Index(
            "uq_single_active_tournament",
            "is_active",
            unique=True,
            postgresql_where=(is_active == True)
        ),
    )

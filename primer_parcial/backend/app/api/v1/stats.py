import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.tournament import Tournament
from app.models.match import Match
from app.models.team import Team
from app.models.player import Player
from app.models.stats import MatchStat
from app.models.user import User
from app.schemas.stats import MatchStatCreate, MatchStatBulkCreate, MatchStatResponse, TopScorerResponse, FairPlayResponse
from app.api.deps import require_admin
from app.services.match_service import MatchService

router = APIRouter()


@router.post("/matches/{match_id}", response_model=List[MatchStatResponse])
async def record_match_stats(
    match_id: uuid.UUID,
    payload: MatchStatBulkCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> Any:
    """
    Carga diferida de estadísticas de jugadores (goles, tarjetas amarillas, tarjetas rojas) para un partido JUGADO.
    """
    stats = await MatchService.record_player_stats(match_id, payload.stats, db)
    return stats


@router.get("/matches/{match_id}", response_model=List[MatchStatResponse])
async def get_match_stats(
    match_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Obtener estadísticas de jugadores registradas para un partido"""
    query = await db.execute(
        select(MatchStat).where(MatchStat.match_id == match_id)
    )
    return query.scalars().all()


@router.get("/top-scorers", response_model=List[TopScorerResponse])
async def get_top_scorers(
    tournament_id: Optional[uuid.UUID] = None,
    limit: int = 15,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Tabla de goleadores del torneo"""
    if not tournament_id:
        active_t = await db.execute(select(Tournament.id).where(Tournament.is_active == True))
        active_id = active_t.scalar_one_or_none()
        if not active_id:
            return []
        tournament_id = active_id

    query = await db.execute(
        select(
            Player.id.label("player_id"),
            func.concat(Player.first_name, " ", Player.last_name).label("player_name"),
            Team.name.label("team_name"),
            Player.jersey_number,
            func.sum(MatchStat.goals).label("goals")
        )
        .join(Player, MatchStat.player_id == Player.id)
        .join(Team, MatchStat.team_id == Team.id)
        .join(Match, MatchStat.match_id == Match.id)
        .where(Match.tournament_id == tournament_id)
        .group_by(Player.id, Player.first_name, Player.last_name, Team.name, Player.jersey_number)
        .having(func.sum(MatchStat.goals) > 0)
        .order_by(desc("goals"), Player.last_name)
        .limit(limit)
    )
    return [
        TopScorerResponse(
            player_id=row.player_id,
            player_name=row.player_name,
            team_name=row.team_name,
            jersey_number=row.jersey_number,
            goals=row.goals
        )
        for row in query.all()
    ]


@router.get("/fair-play", response_model=List[FairPlayResponse])
async def get_fair_play_ranking(
    tournament_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Ranking de Fair Play (tarjetas) por equipo"""
    if not tournament_id:
        active_t = await db.execute(select(Tournament.id).where(Tournament.is_active == True))
        active_id = active_t.scalar_one_or_none()
        if not active_id:
            return []
        tournament_id = active_id

    teams_query = await db.execute(
        select(Team).where(Team.tournament_id == tournament_id, Team.is_active == True)
    )
    teams = list(teams_query.scalars().all())

    stats_query = await db.execute(
        select(
            MatchStat.team_id,
            func.coalesce(func.sum(MatchStat.yellow_cards), 0).label("yellows"),
            func.coalesce(func.sum(MatchStat.red_cards), 0).label("reds")
        )
        .join(Match, MatchStat.match_id == Match.id)
        .where(Match.tournament_id == tournament_id)
        .group_by(MatchStat.team_id)
    )
    stats_dict = {row.team_id: (row.yellows, row.reds) for row in stats_query.all()}

    results = []
    for team in teams:
        yellows, reds = stats_dict.get(team.id, (0, 0))
        # Fair play score: amarilla=1, roja=3
        fp_score = (yellows * 1) + (reds * 3)
        results.append(
            FairPlayResponse(
                team_id=team.id,
                team_name=team.name,
                yellow_cards=yellows,
                red_cards=reds,
                fair_play_score=fp_score
            )
        )

    # Ordenar por menor puntaje de tarjetas (menos tarjetas = mejor fair play)
    results.sort(key=lambda x: (x.fair_play_score, x.red_cards, x.yellow_cards, x.team_name))
    return results

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.tournament import Tournament
from app.models.team import Team
from app.models.round import Round
from app.models.match import Match
from app.models.player import Player
from app.models.stats import MatchStat
from app.models.standings import Standing
from app.schemas.standings import StandingResponse
from app.schemas.match import MatchResponse, RoundResponse
from app.schemas.stats import TopScorerResponse, FairPlayResponse
from app.schemas.team import TeamResponse
from app.api.v1.standings import get_standings
from app.api.v1.stats import get_top_scorers, get_fair_play_ranking

router = APIRouter()


@router.get("/summary")
async def get_public_summary(db: AsyncSession = Depends(get_db)) -> Any:
    """
    Endpoint mobile-first agrupado:
    Devuelve en una única llamada liviana todo lo necesario para renderizar la pantalla inicial:
    torneo activo, tabla de posiciones, próximas fechas y líderes de goleo.
    """
    # 1. Torneo activo
    active_t = await db.execute(select(Tournament).where(Tournament.is_active == True))
    tournament = active_t.scalar_one_or_none()
    if not tournament:
        return {
            "tournament": None,
            "standings": [],
            "recent_results": [],
            "upcoming_matches": [],
            "top_scorers": []
        }

    # 2. Standings
    standings = await get_standings(tournament_id=tournament.id, db=db)

    # 3. Últimos resultados (JUGADO)
    results_query = await db.execute(
        select(Match)
        .options(
            selectinload(Match.home_team),
            selectinload(Match.away_team),
            selectinload(Match.pitch),
            selectinload(Match.round)
        )
        .where(Match.tournament_id == tournament.id, Match.status == "JUGADO")
        .order_by(Match.match_date.desc(), Match.start_time.desc())
        .limit(6)
    )
    recent_results = [MatchResponse.model_validate(m) for m in results_query.scalars().all()]

    # 4. Próximos partidos (PENDIENTE)
    upcoming_query = await db.execute(
        select(Match)
        .options(
            selectinload(Match.home_team),
            selectinload(Match.away_team),
            selectinload(Match.pitch),
            selectinload(Match.round)
        )
        .where(Match.tournament_id == tournament.id, Match.status == "PENDIENTE")
        .order_by(Match.match_date.asc(), Match.start_time.asc())
        .limit(6)
    )
    upcoming_matches = [MatchResponse.model_validate(m) for m in upcoming_query.scalars().all()]

    # 5. Top goleadores
    top_scorers = await get_top_scorers(tournament_id=tournament.id, limit=5, db=db)

    return {
        "tournament": {
            "id": tournament.id,
            "name": tournament.name,
            "start_date": tournament.start_date,
            "fixture_generated": tournament.fixture_generated
        },
        "standings": standings,
        "recent_results": recent_results,
        "upcoming_matches": upcoming_matches,
        "top_scorers": top_scorers
    }


@router.get("/standings", response_model=List[StandingResponse])
async def public_standings(db: AsyncSession = Depends(get_db)) -> Any:
    return await get_standings(db=db)


@router.get("/fixture")
async def public_fixture(db: AsyncSession = Depends(get_db)) -> Any:
    """Fixture completo organizado por fechas"""
    active_t = await db.execute(select(Tournament.id).where(Tournament.is_active == True))
    t_id = active_t.scalar_one_or_none()
    if not t_id:
        return []

    rounds_query = await db.execute(
        select(Round).where(Round.tournament_id == t_id).order_by(Round.round_number)
    )
    rounds = list(rounds_query.scalars().all())

    matches_query = await db.execute(
        select(Match)
        .options(
            selectinload(Match.home_team),
            selectinload(Match.away_team),
            selectinload(Match.pitch)
        )
        .where(Match.tournament_id == t_id)
        .order_by(Match.match_date, Match.start_time, Match.pitch_id)
    )
    all_matches = list(matches_query.scalars().all())

    matches_by_round = {}
    for m in all_matches:
        matches_by_round.setdefault(m.round_id, []).append(MatchResponse.model_validate(m))

    return [
        {
            "round": RoundResponse.model_validate(r),
            "matches": matches_by_round.get(r.id, [])
        }
        for r in rounds
    ]


@router.get("/results", response_model=List[MatchResponse])
async def public_results(db: AsyncSession = Depends(get_db)) -> Any:
    """Listar todos los resultados registrados"""
    active_t = await db.execute(select(Tournament.id).where(Tournament.is_active == True))
    t_id = active_t.scalar_one_or_none()
    if not t_id:
        return []

    query = await db.execute(
        select(Match)
        .options(
            selectinload(Match.home_team),
            selectinload(Match.away_team),
            selectinload(Match.pitch)
        )
        .where(Match.tournament_id == t_id, Match.status == "JUGADO")
        .order_by(Match.match_date.desc(), Match.start_time.desc())
    )
    return [MatchResponse.model_validate(m) for m in query.scalars().all()]


@router.get("/scorers", response_model=List[TopScorerResponse])
async def public_scorers(db: AsyncSession = Depends(get_db)) -> Any:
    return await get_top_scorers(db=db)


@router.get("/cards", response_model=List[FairPlayResponse])
async def public_cards(db: AsyncSession = Depends(get_db)) -> Any:
    return await get_fair_play_ranking(db=db)


@router.get("/teams")
async def public_teams(db: AsyncSession = Depends(get_db)) -> Any:
    """Equipos y planteles habilitados para consulta pública"""
    active_t = await db.execute(select(Tournament.id).where(Tournament.is_active == True))
    t_id = active_t.scalar_one_or_none()
    if not t_id:
        return []

    query = await db.execute(
        select(Team)
        .options(selectinload(Team.players))
        .where(Team.tournament_id == t_id, Team.is_active == True)
        .order_by(Team.name)
    )
    teams = query.scalars().all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "short_name": t.short_name,
            "logo_url": t.logo_url,
            "delegate_name": t.delegate_name,
            "players": [
                {
                    "id": p.id,
                    "first_name": p.first_name,
                    "last_name": p.last_name,
                    "jersey_number": p.jersey_number,
                    "is_enabled": p.is_enabled
                }
                for p in sorted(t.players, key=lambda x: x.jersey_number)
                if p.is_enabled
            ]
        }
        for t in teams
    ]

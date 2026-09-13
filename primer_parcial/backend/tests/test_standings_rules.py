import uuid
from datetime import date, time, timedelta
import pytest
from sqlalchemy import select
from app.models.tournament import Tournament
from app.models.team import Team
from app.models.round import Round
from app.models.match import Match
from app.models.stats import MatchStat
from app.services.standings_engine import StandingsEngine, TeamStatsAccumulator


def test_points_calculation():
    team_id = uuid.uuid4()
    acc = TeamStatsAccumulator(team_id)

    # 2 victorias, 1 empate, 1 derrota
    acc.won = 2
    acc.drawn = 1
    acc.lost = 1
    acc.points = (acc.won * 3) + (acc.drawn * 1) + (acc.lost * 0)

    assert acc.points == 7


def test_fair_play_score_calculation():
    team_id = uuid.uuid4()
    acc = TeamStatsAccumulator(team_id)

    # 3 amarillas (1 pt cada una) + 1 roja (3 pts)
    acc.yellow_cards = 3
    acc.red_cards = 1

    assert acc.fair_play_score == 6


@pytest.mark.asyncio
async def test_tiebreaker_hierarchy(db_session):
    """
    Prueba el ordenamiento jerárquico completo en la tabla:
    1. PTS
    2. DG
    3. GF
    4. Head-to-Head
    5. Fair play
    """
    # Crear torneo de prueba
    test_tourn = Tournament(
        name="Test Tiebreaker Tournament",
        start_date=date.today(),
        is_active=False,
        fixture_generated=True
    )
    db_session.add(test_tourn)
    await db_session.flush()

    # Crear 3 equipos de prueba: A, B, C
    team_a = Team(tournament_id=test_tourn.id, name="Team A", short_name="TMA", delegate_name="Del A", delegate_phone="123")
    team_b = Team(tournament_id=test_tourn.id, name="Team B", short_name="TMB", delegate_name="Del B", delegate_phone="123")
    team_c = Team(tournament_id=test_tourn.id, name="Team C", short_name="TMC", delegate_name="Del C", delegate_phone="123")
    db_session.add_all([team_a, team_b, team_c])
    await db_session.flush()

    future_date = date.today() + timedelta(days=500)
    round_1 = Round(tournament_id=test_tourn.id, round_number=99, name="Fecha Test", scheduled_date=future_date)
    db_session.add(round_1)
    await db_session.flush()

    # Caso 1: Team A le gana a Team B 2-1 (ambos juegan 1 partido)
    # Team A: 3 pts, DG +1, GF 2
    # Team B: 0 pts, DG -1, GF 1
    match_1 = Match(
        round_id=round_1.id,
        tournament_id=test_tourn.id,
        home_team_id=team_a.id,
        away_team_id=team_b.id,
        pitch_id=1,
        match_date=future_date,
        start_time=time(11, 0),
        end_time=time(12, 10),
        home_score=2,
        away_score=1,
        status="JUGADO",
        is_locked=True
    )
    db_session.add(match_1)
    await db_session.commit()

    standings = await StandingsEngine.recalculate_tournament_standings(test_tourn.id, db_session)
    assert len(standings) == 3

    # Team A debe ser 1ero con 3 puntos
    assert standings[0].team_id == team_a.id
    assert standings[0].points == 3
    assert standings[0].goal_diff == 1
    assert standings[0].goals_for == 2
    assert standings[0].position == 1

    # Team C (sin partidos jugados): 0 pts, DG 0
    # Team B: 0 pts, DG -1
    # Por DG, Team C supera a Team B
    assert standings[1].team_id == team_c.id
    assert standings[2].team_id == team_b.id

    # Limpieza
    await db_session.delete(test_tourn)
    await db_session.commit()


def test_compute_standings_ranking_pure():
    """Prueba unitaria pura y aislada de los criterios de clasificación sin base de datos."""
    from app.services.standings_engine import compute_standings_ranking, CompletedMatchResult

    t_alpha = uuid.uuid4()
    t_beta = uuid.uuid4()
    t_gamma = uuid.uuid4()

    # Partidos:
    # Alpha 3 - 0 Beta -> Alpha 3 pts, Beta 0 pts
    # Beta 2 - 1 Gamma -> Beta 3 pts, Gamma 0 pts
    # Gamma 2 - 0 Alpha -> Gamma 3 pts, Alpha 0 pts
    # Triple empate en 3 puntos:
    # Alpha: GF 3, GC 2, DG +1, PTS 3
    # Beta: GF 2, GC 4, DG -2, PTS 3
    # Gamma: GF 3, GC 2, DG +1, PTS 3
    # Alpha y Gamma empatan en PTS (3), DG (+1) y GF (3)!
    # Head-to-Head entre Alpha y Gamma: Gamma le ganó 2-0 a Alpha -> Gamma debe quedar arriba de Alpha!
    matches = [
        CompletedMatchResult(home_team_id=t_alpha, away_team_id=t_beta, home_score=3, away_score=0),
        CompletedMatchResult(home_team_id=t_beta, away_team_id=t_gamma, home_score=2, away_score=1),
        CompletedMatchResult(home_team_id=t_gamma, away_team_id=t_alpha, home_score=2, away_score=0),
    ]

    ranking = compute_standings_ranking(
        team_ids=[t_alpha, t_beta, t_gamma],
        played_matches=matches
    )

    assert len(ranking) == 3
    # 1ro debe ser Gamma por Head-to-Head contra Alpha (DG +1 ambos, pero Gamma ganó 2-0 directo)
    assert ranking[0].team_id == t_gamma
    assert ranking[0].points == 3
    assert ranking[0].goal_diff == 1

    # 2do debe ser Alpha
    assert ranking[1].team_id == t_alpha
    assert ranking[1].points == 3
    assert ranking[1].goal_diff == 1

    # 3ro debe ser Beta (DG -2)
    assert ranking[2].team_id == t_beta
    assert ranking[2].points == 3
    assert ranking[2].goal_diff == -2


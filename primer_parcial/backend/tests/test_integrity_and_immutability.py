import uuid
from datetime import date, time
import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from app.models.tournament import Tournament
from app.models.team import Team
from app.models.player import Player
from app.models.match import Match
from app.models.round import Round
from app.schemas.match import MatchResultUpdate
from app.services.match_service import MatchService
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_match_result_immutability_via_service(db_session):
    """Verifica que el servicio rechaza con 409 modificar el resultado de un partido ya jugado"""
    # Buscar un partido ya jugado
    query = await db_session.execute(select(Match).where(Match.status == "JUGADO").limit(1))
    match = query.scalar_one_or_none()
    assert match is not None

    with pytest.raises(HTTPException) as exc_info:
        await MatchService.record_result(
            match.id,
            MatchResultUpdate(home_score=9, away_score=9),
            db_session
        )
    assert exc_info.value.status_code == 409
    assert "inmutable" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_match_result_immutability_via_postgresql_trigger(db_session):
    """Verifica que el trigger trg_match_score_immutability de PostgreSQL bloquea UPDATEs directos"""
    query = await db_session.execute(select(Match).where(Match.status == "JUGADO").limit(1))
    match = query.scalar_one_or_none()
    assert match is not None

    # Intentar update crudo por SQL
    with pytest.raises(DBAPIError) as exc_info:
        await db_session.execute(
            text(f"UPDATE matches SET home_score = home_score + 10 WHERE id = '{match.id}';")
        )
        await db_session.commit()

    # Revertir transacción fallida
    await db_session.rollback()
    assert "inmutable" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_player_unique_dni_constraint(db_session):
    """Verifica que no se pueden registrar dos jugadores con el mismo DNI en el torneo"""
    query = await db_session.execute(select(Player).limit(1))
    existing_player = query.scalar_one_or_none()
    assert existing_player is not None

    duplicate_player = Player(
        team_id=existing_player.team_id,
        first_name="Clon",
        last_name="Test",
        dni=existing_player.dni,  # Mismo DNI
        birth_date=date(1995, 1, 1),
        jersey_number=99,
        is_enabled=True
    )
    db_session.add(duplicate_player)

    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_player_unique_jersey_per_team_constraint(db_session):
    """Verifica que el número de camiseta no puede repetirse dentro de un mismo equipo"""
    query = await db_session.execute(select(Player).limit(1))
    existing_player = query.scalar_one_or_none()
    assert existing_player is not None

    duplicate_jersey_player = Player(
        team_id=existing_player.team_id,
        first_name="Otro",
        last_name="Jugador",
        dni="99999999",  # DNI distinto
        birth_date=date(1995, 1, 1),
        jersey_number=existing_player.jersey_number,  # Misma camiseta en el mismo equipo
        is_enabled=True
    )
    db_session.add(duplicate_jersey_player)

    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

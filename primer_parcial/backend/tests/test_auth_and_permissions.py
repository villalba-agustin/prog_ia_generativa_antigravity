import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models.team import Team
from app.models.match import Match


@pytest.mark.asyncio
async def test_public_endpoints_require_no_auth(client: AsyncClient):
    """La sección pública no requiere usuario ni token"""
    res_summary = await client.get("/api/v1/public/summary")
    assert res_summary.status_code == 200

    res_standings = await client.get("/api/v1/public/standings")
    assert res_standings.status_code == 200

    res_fixture = await client.get("/api/v1/public/fixture")
    assert res_fixture.status_code == 200

    res_scorers = await client.get("/api/v1/public/scorers")
    assert res_scorers.status_code == 200

    res_cards = await client.get("/api/v1/public/cards")
    assert res_cards.status_code == 200

    res_teams = await client.get("/api/v1/public/teams")
    assert res_teams.status_code == 200


@pytest.mark.asyncio
async def test_delegate_cannot_modify_other_team(client: AsyncClient, db_session, make_delegate_headers):
    """El delegado sólo podrá acceder a la información y operaciones permitidas sobre su equipo"""
    teams = (await db_session.execute(select(Team).limit(2))).scalars().all()
    assert len(teams) >= 2
    team_a, team_b = teams[0], teams[1]

    # Delegado del Team A
    headers_del_a = await make_delegate_headers(team_a.id)

    # Intentar modificar Team B con credenciales del Delegado A -> 403 Forbidden
    res = await client.put(
        f"/api/v1/teams/{team_b.id}",
        json={"delegate_name": "Intruso", "delegate_phone": "999999"},
        headers=headers_del_a
    )
    assert res.status_code == 403

    # Modificar su propio Team A -> 200 OK
    res_own = await client.put(
        f"/api/v1/teams/{team_a.id}",
        json={"delegate_name": "Delegado Actualizado", "delegate_phone": "381-999999"},
        headers=headers_del_a
    )
    assert res_own.status_code == 200
    assert res_own.json()["delegate_name"] == "Delegado Actualizado"


@pytest.mark.asyncio
async def test_delegate_cannot_record_match_result(client: AsyncClient, db_session, make_delegate_headers):
    """El delegado no puede cargar resultados (operación exclusiva de Administrador)"""
    team = (await db_session.execute(select(Team).limit(1))).scalar_one()
    match = (await db_session.execute(select(Match).where(Match.status == "PENDIENTE").limit(1))).scalar_one()

    headers_del = await make_delegate_headers(team.id)

    res = await client.post(
        f"/api/v1/matches/{match.id}/result",
        json={"home_score": 1, "away_score": 0},
        headers=headers_del
    )
    assert res.status_code == 403

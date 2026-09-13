"""
Test suite for all 9 MCP tools in Liga de Barrios y Fincas.
Tests tool execution directly and via MCPServer interface.
"""

import pytest
from server import server
from tools.schema import get_database_schema
from tools.teams import list_teams, list_players
from tools.tournament import get_tournament_summary, get_standings
from tools.fixture import get_matchday, validate_fixture
from tools.stats import get_top_scorers, get_card_statistics

pytestmark = pytest.mark.asyncio

# 1. Test get_database_schema
async def test_get_database_schema():
    res = await get_database_schema()
    assert res["database"] == "liga_barrios"
    assert "tables" in res
    tables = res["tables"]
    # Check that core domain tables are exposed
    for expected_table in ["tournaments", "teams", "players", "rounds", "matches", "standings"]:
        assert expected_table in tables
        t_data = tables[expected_table]
        assert "columns" in t_data
        assert "primary_key" in t_data
        assert len(t_data["columns"]) > 0

    # Ensure sensitive tables like 'users' are not exposed
    assert "users" not in tables
    assert "alembic_version" not in tables

# 2. Test list_teams
async def test_list_teams():
    teams = await list_teams(include_inactive=True)
    assert isinstance(teams, list)
    assert len(teams) >= 8  # 8 teams seeded
    first = teams[0]
    for key in ["id", "name", "short_name", "delegate_name", "delegate_phone", "player_count"]:
        assert key in first
    assert first["player_count"] >= 0

# 3. Test list_players
async def test_list_players_all():
    players = await list_players()
    assert isinstance(players, list)
    assert len(players) >= 50
    first = players[0]
    for key in ["id", "full_name", "dni", "jersey_number", "team_name"]:
        assert key in first

async def test_list_players_filter_by_name():
    teams = await list_teams()
    sample_team = teams[0]["name"]
    filtered = await list_players(team_name=sample_team)
    assert len(filtered) > 0
    for p in filtered:
        assert p["team_name"].lower() == sample_team.lower()

async def test_list_players_invalid_uuid():
    res = await list_players(team_id="invalid-uuid-123")
    assert len(res) == 1
    assert "error" in res[0]

# 4. Test get_tournament_summary
async def test_get_tournament_summary():
    summary = await get_tournament_summary()
    assert "tournament" in summary
    assert "summary" in summary
    s = summary["summary"]
    assert s["total_teams"] == 8
    assert s["total_players"] >= 70
    assert s["total_rounds"] == 7
    assert s["total_matches"] == 28
    assert s["matches_played"] >= 0
    assert s["matches_pending"] >= 0
    assert s["matches_played"] + s["matches_pending"] + s["matches_suspended"] + s["matches_cancelled"] == 28

# 5. Test get_standings
async def test_get_standings():
    standings = await get_standings()
    assert isinstance(standings, list)
    assert len(standings) == 8
    for row in standings:
        for metric in ["position", "team", "PJ", "PG", "PE", "PP", "GF", "GC", "DG", "PTS"]:
            assert metric in row
        # Arithmetic sanity check: PJ = PG + PE + PP
        assert row["PJ"] == row["PG"] + row["PE"] + row["PP"]
        # Arithmetic check: DG = GF - GC
        assert row["DG"] == row["GF"] - row["GC"]

# 6. Test get_matchday
async def test_get_matchday_valid():
    md = await get_matchday(round_number=1)
    assert "error" not in md
    assert md["round_number"] == 1
    assert md["total_matches"] == 4  # 8 teams / 2 = 4 matches per round
    matches = md["matches"]
    assert len(matches) == 4
    first_match = matches[0]
    assert "home_team" in first_match
    assert "away_team" in first_match
    assert "pitch" in first_match
    assert "schedule" in first_match
    assert "status" in first_match

async def test_get_matchday_invalid_number():
    md = await get_matchday(round_number=999)
    assert "error" in md

async def test_get_matchday_negative():
    md = await get_matchday(round_number=0)
    assert "error" in md

# 7. Test validate_fixture
async def test_validate_fixture():
    val = await validate_fixture()
    assert "is_valid" in val
    assert val["is_valid"] is True
    assert val["total_teams"] == 8
    assert val["total_matches"] == 28
    assert val["duplicate_matchups_count"] == 0
    assert val["team_double_bookings_count"] == 0
    assert val["pitch_conflicts_count"] == 0
    assert val["schedule_conflicts_count"] == 0
    assert len(val["matches_per_round"]) == 7
    # 4 matches in every round
    for rn, count in val["matches_per_round"].items():
        assert count == 4
    assert val["inconsistencies_count"] == 0

# 8. Test get_top_scorers
async def test_get_top_scorers():
    scorers = await get_top_scorers(limit=5)
    assert isinstance(scorers, list)
    for s in scorers:
        assert "player_name" in s
        assert "team_name" in s
        assert "goals" in s
        assert s["goals"] > 0

# 9. Test get_card_statistics
async def test_get_card_statistics_team():
    stats = await get_card_statistics(group_by="team")
    assert "cards_by_team" in stats
    assert "cards_by_player" not in stats
    assert len(stats["cards_by_team"]) == 8

async def test_get_card_statistics_invalid_group():
    stats = await get_card_statistics(group_by="referee")
    assert "error" in stats

# 10. Test MCPServer protocol interface
async def test_mcp_server_interface_call_tools():
    # Test that the MCPServer instance calls tools cleanly and returns valid CallToolResult
    res = await server.call_tool("get_tournament_summary", {})
    assert res is not None
    assert len(res.content) > 0

    res_teams = await server.call_tool("list_teams", {"include_inactive": False})
    assert res_teams is not None
    assert len(res_teams.content) > 0

    res_val = await server.call_tool("validate_fixture", {})
    assert res_val is not None
    assert len(res_val.content) > 0

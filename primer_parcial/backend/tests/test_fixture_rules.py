import uuid
from datetime import time, timedelta, datetime
import pytest
from app.services.fixture_engine import generate_round_robin_pairings, MATCH_SLOTS, MATCH_DURATION_MINUTES
from app.models.pitch import Pitch


def test_round_robin_pairings_even_teams():
    # 8 equipos
    team_ids = [uuid.uuid4() for _ in range(8)]
    rounds = generate_round_robin_pairings(team_ids)

    # N-1 = 7 fechas
    assert len(rounds) == 7

    # Cada fecha debe tener N/2 = 4 partidos
    all_pairs = []
    for r_idx, r in enumerate(rounds):
        assert len(r) == 4, f"La fecha {r_idx} debería tener 4 partidos"
        teams_in_round = set()
        for home, away in r:
            assert home != away, "Un equipo no puede jugar contra sí mismo"
            assert home not in teams_in_round, f"Equipo {home} duplicado en la fecha {r_idx}"
            assert away not in teams_in_round, f"Equipo {away} duplicado en la fecha {r_idx}"
            teams_in_round.add(home)
            teams_in_round.add(away)

            # Normalizar para verificar ausencia de enfrentamientos duplicados
            pair_key = tuple(sorted([str(home), str(away)]))
            all_pairs.append(pair_key)

    # Total de partidos: 8 * 7 / 2 = 28
    assert len(all_pairs) == 28
    # Ausencia total de enfrentamientos duplicados
    assert len(set(all_pairs)) == 28


def test_round_robin_pairings_odd_teams():
    # 7 equipos (impar: debe generar fecha libre sin solapar)
    team_ids = [uuid.uuid4() for _ in range(7)]
    rounds = generate_round_robin_pairings(team_ids)

    # Con 7 equipos, son 7 fechas
    assert len(rounds) == 7

    all_pairs = []
    for r_idx, r in enumerate(rounds):
        assert len(r) == 3  # 1 equipo queda libre cada fecha
        teams_in_round = set()
        for home, away in r:
            assert home != away
            assert home not in teams_in_round
            assert away not in teams_in_round
            teams_in_round.add(home)
            teams_in_round.add(away)
            pair_key = tuple(sorted([str(home), str(away)]))
            all_pairs.append(pair_key)

    # 7 * 6 / 2 = 21 partidos
    assert len(all_pairs) == 21
    assert len(set(all_pairs)) == 21


def test_time_slots_rules():
    # Duración de 70 minutos estricta: 30' PT + 10' ET + 30' ST
    assert MATCH_DURATION_MINUTES == 70

    # Todos los slots deben comenzar entre 11:00 y terminar a las 18:00
    assert len(MATCH_SLOTS) == 6
    assert MATCH_SLOTS[0][0] == time(11, 0)
    assert MATCH_SLOTS[-1][1] == time(18, 0)

    # Verificar que cada slot dura exactamente 70 minutos
    for idx, (start_t, end_t) in enumerate(MATCH_SLOTS):
        dt_start = datetime.combine(datetime.today(), start_t)
        dt_end = datetime.combine(datetime.today(), end_t)
        duration_minutes = (dt_end - dt_start).total_seconds() / 60
        assert duration_minutes == 70, f"El slot {idx} debe durar exactamente 70 minutos"

    # Verificar que no hay solapamiento entre slots consecutivos
    for i in range(len(MATCH_SLOTS) - 1):
        assert MATCH_SLOTS[i][1] == MATCH_SLOTS[i + 1][0], "Los slots deben ser continuos y no solaparse"


@pytest.mark.asyncio
async def test_database_seeded_fixture_integrity(db_session):
    """Verifica que el fixture generado en PostgreSQL respeta las reglas críticas de capacidad y unicidad"""
    from sqlalchemy import select
    from app.models.match import Match
    from app.models.round import Round

    # Obtener todas las rondas
    rounds = (await db_session.execute(select(Round))).scalars().all()
    assert len(rounds) > 0

    all_matches = (await db_session.execute(select(Match))).scalars().all()
    assert len(all_matches) > 0

    # 1. Ausencia de enfrentamientos duplicados
    seen_pairings = set()
    for m in all_matches:
        pair = tuple(sorted([str(m.home_team_id), str(m.away_team_id)]))
        assert pair not in seen_pairings, f"Enfrentamiento duplicado encontrado: {pair}"
        seen_pairings.add(pair)

    # 2. Capacidad de canchas: solo canchas 1 a 4
    for m in all_matches:
        assert m.pitch_id in [1, 2, 3, 4]

    # 3. Ningún equipo dos veces por fecha
    matches_by_round = {}
    for m in all_matches:
        matches_by_round.setdefault(m.round_id, []).append(m)

    for round_id, matches in matches_by_round.items():
        teams_in_round = []
        for m in matches:
            assert m.home_team_id not in teams_in_round, f"Equipo {m.home_team_id} juega dos veces en round {round_id}"
            assert m.away_team_id not in teams_in_round, f"Equipo {m.away_team_id} juega dos veces en round {round_id}"
            teams_in_round.append(m.home_team_id)
            teams_in_round.append(m.away_team_id)

    # 4. Ausencia de solapamiento en canchas para la misma fecha
    for round_id, matches in matches_by_round.items():
        pitch_times = set()
        for m in matches:
            key = (m.pitch_id, m.match_date, m.start_time)
            assert key not in pitch_times, f"Solapamiento detectado en cancha {m.pitch_id} a las {m.start_time}"
            pitch_times.add(key)

"""
Tools: get_matchday, validate_fixture
Fixture querying and comprehensive fixture integrity validation for Liga de Barrios y Fincas.
"""

from typing import Dict, Any, List
from collections import defaultdict
from sqlalchemy import text
from db import get_db_connection

async def get_matchday(round_number: int) -> Dict[str, Any]:
    """
    Recibe el número de fecha y devuelve todos sus partidos, horarios, canchas, equipos y estados.
    
    Args:
        round_number: Número de la fecha a consultar (ej: 1, 2, ...).
    """
    if round_number < 1:
        return {
            "error": f"El número de fecha debe ser mayor o igual a 1. Se recibió {round_number}."
        }

    async with get_db_connection() as conn:
        # Find the round in active tournament
        r_query = text("""
            SELECT r.id, r.round_number, r.name, r.scheduled_date, r.status, t.name as tournament_name
            FROM rounds r
            JOIN tournaments t ON r.tournament_id = t.id
            WHERE t.is_active = TRUE AND r.round_number = :rn
            LIMIT 1;
        """)
        r_res = await conn.execute(r_query, {"rn": round_number})
        round_row = r_res.fetchone()

        if not round_row:
            return {
                "error": f"No se encontró la fecha número {round_number} en el torneo activo."
            }

        # Find matches for this round
        m_query = text("""
            SELECT 
                m.id,
                ht.name as home_team_name,
                ht.short_name as home_team_short,
                at.name as away_team_name,
                at.short_name as away_team_short,
                p.pitch_number,
                p.name as pitch_name,
                m.match_date,
                m.start_time,
                m.end_time,
                m.home_score,
                m.away_score,
                m.status,
                m.is_locked
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            JOIN pitches p ON m.pitch_id = p.id
            WHERE m.round_id = :rid
            ORDER BY m.match_date ASC, m.start_time ASC, p.pitch_number ASC;
        """)
        m_res = await conn.execute(m_query, {"rid": round_row.id})
        matches_rows = m_res.fetchall()

        matches_list = []
        for m in matches_rows:
            matches_list.append({
                "match_id": str(m.id),
                "home_team": {
                    "name": m.home_team_name,
                    "short_name": m.home_team_short
                },
                "away_team": {
                    "name": m.away_team_name,
                    "short_name": m.away_team_short
                },
                "pitch": {
                    "number": m.pitch_number,
                    "name": m.pitch_name
                },
                "schedule": {
                    "date": m.match_date.isoformat() if m.match_date else None,
                    "start_time": m.start_time.strftime("%H:%M") if m.start_time else None,
                    "end_time": m.end_time.strftime("%H:%M") if m.end_time else None,
                },
                "score": {
                    "home": m.home_score,
                    "away": m.away_score
                },
                "status": m.status,
                "is_locked": m.is_locked
            })

        return {
            "round_number": round_row.round_number,
            "round_name": round_row.name,
            "scheduled_date": round_row.scheduled_date.isoformat() if round_row.scheduled_date else None,
            "round_status": round_row.status,
            "tournament_name": round_row.tournament_name,
            "total_matches": len(matches_list),
            "matches": matches_list
        }

async def validate_fixture() -> Dict[str, Any]:
    """
    Analiza el fixture completo del torneo activo y devuelve un diagnóstico estructurado indicando:
    - si el fixture es válido
    - número total de partidos
    - cantidad de enfrentamientos duplicados
    - equipos que juegan más de una vez en una fecha
    - conflictos de horarios por equipo
    - conflictos de cancha (misma cancha en horarios superpuestos)
    - cantidad de partidos por fecha
    - cualquier otra inconsistencia relevante
    """
    async with get_db_connection() as conn:
        # 1. Fetch active tournament
        t_res = await conn.execute(text("""
            SELECT id, name, fixture_generated FROM tournaments WHERE is_active = TRUE LIMIT 1;
        """))
        tourney = t_res.fetchone()
        if not tourney:
            return {
                "is_valid": False,
                "error": "No hay ningún torneo activo para validar."
            }

        tourney_id = tourney.id

        # 2. Fetch all registered teams
        teams_res = await conn.execute(
            text("SELECT id, name, is_active FROM teams WHERE tournament_id = :tid;"),
            {"tid": tourney_id}
        )
        teams = teams_res.fetchall()
        teams_map = {str(t.id): t.name for t in teams}
        total_teams = len(teams)

        # 3. Fetch all matches with details
        matches_query = text("""
            SELECT 
                m.id,
                m.round_id,
                r.round_number,
                m.home_team_id,
                m.away_team_id,
                ht.name as home_name,
                at.name as away_name,
                m.pitch_id,
                p.pitch_number,
                p.name as pitch_name,
                m.match_date,
                m.start_time,
                m.end_time,
                m.status
            FROM matches m
            JOIN rounds r ON m.round_id = r.id
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            JOIN pitches p ON m.pitch_id = p.id
            WHERE m.tournament_id = :tid
            ORDER BY r.round_number, m.match_date, m.start_time;
        """)
        matches_res = await conn.execute(matches_query, {"tid": tourney_id})
        matches = matches_res.fetchall()
        total_matches = len(matches)

        inconsistencies = []

        # Check: expected match count for single round-robin
        # Formula: N * (N - 1) / 2
        expected_matches = (total_teams * (total_teams - 1)) // 2 if total_teams >= 2 else 0
        if total_matches != expected_matches:
            inconsistencies.append(
                f"Cantidad de partidos ({total_matches}) difiere de lo esperado para {total_teams} equipos en 1 rueda ({expected_matches} partidos)."
            )

        # 4. Check duplicate matchups (regardless of home/away)
        pair_counts = defaultdict(list)
        for m in matches:
            t1, t2 = sorted([str(m.home_team_id), str(m.away_team_id)])
            pair_counts[(t1, t2)].append({
                "match_id": str(m.id),
                "round_number": m.round_number,
                "home": m.home_name,
                "away": m.away_name
            })

        duplicate_matchups = []
        for (t1, t2), occurrences in pair_counts.items():
            if len(occurrences) > 1:
                duplicate_matchups.append({
                    "team_1": teams_map.get(t1, t1),
                    "team_2": teams_map.get(t2, t2),
                    "count": len(occurrences),
                    "occurrences": occurrences
                })
                inconsistencies.append(
                    f"Enfrentamiento repetido ({len(occurrences)} veces): {teams_map.get(t1, t1)} vs {teams_map.get(t2, t2)}"
                )

        # 5. Check team double bookings in the same round
        # A team must play at most once per round
        round_team_matches = defaultdict(lambda: defaultdict(list))
        matches_per_round = defaultdict(int)

        for m in matches:
            rn = m.round_number
            matches_per_round[rn] += 1
            round_team_matches[rn][str(m.home_team_id)].append(str(m.id))
            round_team_matches[rn][str(m.away_team_id)].append(str(m.id))

        team_double_bookings = []
        for rn, team_matches in round_team_matches.items():
            for tid, m_ids in team_matches.items():
                if len(m_ids) > 1:
                    t_name = teams_map.get(tid, tid)
                    team_double_bookings.append({
                        "team": t_name,
                        "round_number": rn,
                        "matches_count": len(m_ids),
                        "match_ids": m_ids
                    })
                    inconsistencies.append(
                        f"Equipo '{t_name}' juega {len(m_ids)} partidos en la Fecha {rn}."
                    )

        # 6. Check pitch overlaps (same pitch, same date, overlapping time slots)
        pitch_conflicts = []
        pitch_slots = defaultdict(list)
        for m in matches:
            key = (m.pitch_number, m.match_date)
            pitch_slots[key].append(m)

        for (p_num, m_date), slot_matches in pitch_slots.items():
            if len(slot_matches) > 1:
                for i in range(len(slot_matches)):
                    for j in range(i + 1, len(slot_matches)):
                        m1 = slot_matches[i]
                        m2 = slot_matches[j]
                        # Check overlap: m1.start < m2.end and m2.start < m1.end
                        if m1.start_time < m2.end_time and m2.start_time < m1.end_time:
                            pitch_conflicts.append({
                                "pitch_number": p_num,
                                "date": m_date.isoformat(),
                                "match_1": {
                                    "id": str(m1.id),
                                    "teams": f"{m1.home_name} vs {m1.away_name}",
                                    "time": f"{m1.start_time.strftime('%H:%M')}-{m1.end_time.strftime('%H:%M')}"
                                },
                                "match_2": {
                                    "id": str(m2.id),
                                    "teams": f"{m2.home_name} vs {m2.away_name}",
                                    "time": f"{m2.start_time.strftime('%H:%M')}-{m2.end_time.strftime('%H:%M')}"
                                }
                            })
                            inconsistencies.append(
                                f"Conflicto de cancha {p_num} el {m_date}: superposición entre partido ({m1.home_name} vs {m1.away_name}) y ({m2.home_name} vs {m2.away_name})."
                            )

        # 7. Check team schedule overlap across all matches on same date
        schedule_conflicts = []
        team_slots = defaultdict(list)
        for m in matches:
            team_slots[(str(m.home_team_id), m.match_date)].append(m)
            team_slots[(str(m.away_team_id), m.match_date)].append(m)

        for (tid, m_date), t_matches in team_slots.items():
            if len(t_matches) > 1:
                for i in range(len(t_matches)):
                    for j in range(i + 1, len(t_matches)):
                        m1 = t_matches[i]
                        m2 = t_matches[j]
                        if m1.id != m2.id and m1.start_time < m2.end_time and m2.start_time < m1.end_time:
                            t_name = teams_map.get(tid, tid)
                            schedule_conflicts.append({
                                "team": t_name,
                                "date": m_date.isoformat(),
                                "conflict": f"Superposición horaria entre partidos {m1.id} y {m2.id}"
                            })
                            inconsistencies.append(
                                f"Conflicto horario para '{t_name}' el {m_date}."
                            )

        # 8. Check team self-matches
        for m in matches:
            if m.home_team_id == m.away_team_id:
                inconsistencies.append(
                    f"Partido inválido: el equipo '{m.home_name}' juega contra sí mismo en el partido {m.id}."
                )

        is_valid = (
            len(duplicate_matchups) == 0
            and len(team_double_bookings) == 0
            and len(pitch_conflicts) == 0
            and len(schedule_conflicts) == 0
            and len(inconsistencies) == 0
        )

        return {
            "is_valid": is_valid,
            "tournament_name": tourney.name,
            "total_teams": total_teams,
            "total_matches": total_matches,
            "expected_matches_for_round_robin": expected_matches,
            "duplicate_matchups_count": len(duplicate_matchups),
            "duplicate_matchups": duplicate_matchups,
            "team_double_bookings_count": len(team_double_bookings),
            "team_double_bookings": team_double_bookings,
            "pitch_conflicts_count": len(pitch_conflicts),
            "pitch_conflicts": pitch_conflicts,
            "schedule_conflicts_count": len(schedule_conflicts),
            "schedule_conflicts": schedule_conflicts,
            "matches_per_round": dict(sorted(matches_per_round.items())),
            "inconsistencies_count": len(inconsistencies),
            "inconsistencies": inconsistencies,
            "validation_summary": "Fixture 100% válido y consistente." if is_valid else f"Se detectaron {len(inconsistencies)} inconsistencias en el fixture."
        }

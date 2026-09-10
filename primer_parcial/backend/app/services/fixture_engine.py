import uuid
from datetime import date, time, timedelta, datetime
from typing import List, Tuple, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.tournament import Tournament
from app.models.team import Team
from app.models.round import Round
from app.models.match import Match
from app.models.pitch import Pitch
from app.models.standings import Standing

# Constantes del reglamento del torneo
MATCH_DURATION_MINUTES = 70  # 30' PT + 10' ET + 30' ST
START_HOUR = 11
END_HOUR = 18

# Slots calculados: 11:00 a 18:00 en intervalos de 70 min
# Exactamente 6 slots por día
MATCH_SLOTS: List[Tuple[time, time]] = [
    (time(11, 0), time(12, 10)),
    (time(12, 10), time(13, 20)),
    (time(13, 20), time(14, 30)),
    (time(14, 30), time(15, 40)),
    (time(15, 40), time(16, 50)),
    (time(16, 50), time(18, 0)),
]


def generate_round_robin_pairings(team_ids: List[uuid.UUID]) -> List[List[Tuple[uuid.UUID, uuid.UUID]]]:
    """
    Algoritmo de Berger (Round-Robin canonical).
    Genera los emparejamientos para que cada equipo juegue exactamente una vez contra cada uno.
    Si el número de equipos es impar, se agrega un None (fecha libre / bye).
    """
    teams = list(team_ids)
    n = len(teams)
    if n % 2 != 0:
        teams.append(None)
        n += 1

    rounds: List[List[Tuple[uuid.UUID, uuid.UUID]]] = []
    current_teams = list(teams)

    for round_idx in range(n - 1):
        round_matches: List[Tuple[uuid.UUID, uuid.UUID]] = []
        for match_idx in range(n // 2):
            home = current_teams[match_idx]
            away = current_teams[n - 1 - match_idx]

            # Alternar localía en rondas impares para el equipo fijo en pos 0
            if match_idx == 0 and round_idx % 2 == 1:
                home, away = away, home

            if home is not None and away is not None:
                round_matches.append((home, away))

        rounds.append(round_matches)
        # Rotar elementos excepto el primero (current_teams[0])
        current_teams = [current_teams[0]] + [current_teams[-1]] + current_teams[1:-1]

    return rounds


class FixtureEngine:
    @staticmethod
    async def generate_fixture_for_tournament(
        tournament_id: uuid.UUID,
        db: AsyncSession
    ) -> List[Round]:
        # 1. Obtener torneo
        tournament_query = await db.execute(
            select(Tournament).where(Tournament.id == tournament_id)
        )
        tournament = tournament_query.scalar_one_or_none()
        if not tournament:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Torneo no encontrado"
            )

        if tournament.fixture_generated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El fixture ya fue generado para este torneo y no se puede regenerar"
            )

        # 2. Obtener equipos activos
        teams_query = await db.execute(
            select(Team).where(Team.tournament_id == tournament_id, Team.is_active == True)
        )
        teams = list(teams_query.scalars().all())
        if len(teams) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requieren al menos 2 equipos activos para generar el fixture"
            )

        # 3. Obtener canchas (deben ser 4)
        pitches_query = await db.execute(
            select(Pitch).where(Pitch.is_available == True).order_by(Pitch.pitch_number)
        )
        pitches = list(pitches_query.scalars().all())
        if not pitches:
            # Si no hay canchas en la base de datos, crear las 4 canchas reglamentarias
            for i in range(1, 5):
                pitch = Pitch(id=i, name=f"Cancha {i}", pitch_number=i, is_available=True)
                db.add(pitch)
            await db.flush()
            pitches_query = await db.execute(
                select(Pitch).where(Pitch.is_available == True).order_by(Pitch.pitch_number)
            )
            pitches = list(pitches_query.scalars().all())

        team_ids = [t.id for t in teams]
        pairings_by_round = generate_round_robin_pairings(team_ids)

        created_rounds: List[Round] = []
        base_date = tournament.start_date
        num_pitches = len(pitches)
        slots_count = len(MATCH_SLOTS)

        # Inicializar o asegurar entradas en la tabla de posiciones para todos los equipos
        for team in teams:
            standing_check = await db.execute(
                select(Standing).where(Standing.tournament_id == tournament_id, Standing.team_id == team.id)
            )
            if not standing_check.scalar_one_or_none():
                db.add(Standing(
                    tournament_id=tournament_id,
                    team_id=team.id,
                    played=0, won=0, drawn=0, lost=0,
                    goals_for=0, goals_against=0, goal_diff=0,
                    points=0, fair_play_score=0, position=1
                ))

        # 4. Generar fechas y partidos respetando 4 canchas y slots de 70 min
        for round_idx, pairings in enumerate(pairings_by_round):
            round_date = base_date + timedelta(days=round_idx * 7)  # Cada fecha en fines de semana consecutivos
            round_obj = Round(
                tournament_id=tournament_id,
                round_number=round_idx + 1,
                name=f"Fecha {round_idx + 1}",
                scheduled_date=round_date,
                status="PENDIENTE"
            )
            db.add(round_obj)
            await db.flush()  # Obtener ID de la ronda

            # Asignar canchas y slots a cada partido de la fecha
            # Usamos una rotación para equilibrar canchas y horarios
            for match_idx, (home_id, away_id) in enumerate(pairings):
                pitch_index = match_idx % num_pitches
                slot_index = (match_idx // num_pitches) % slots_count
                
                pitch = pitches[pitch_index]
                start_t, end_t = MATCH_SLOTS[slot_index]

                match_obj = Match(
                    round_id=round_obj.id,
                    tournament_id=tournament_id,
                    home_team_id=home_id,
                    away_team_id=away_id,
                    pitch_id=pitch.id,
                    match_date=round_date,
                    start_time=start_t,
                    end_time=end_t,
                    status="PENDIENTE",
                    is_locked=False
                )
                db.add(match_obj)

            created_rounds.append(round_obj)

        tournament.fixture_generated = True
        await db.commit()
        return created_rounds

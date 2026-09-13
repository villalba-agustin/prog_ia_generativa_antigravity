"""
Motor de generación de fixture para Liga de Barrios y Fincas.
Aplica el algoritmo de Berger (Round-Robin canonical a una sola rueda)
y distribuye los partidos entre las 4 canchas oficiales y las franjas horarias reglamentarias.
"""

import uuid
from dataclasses import dataclass
from datetime import date, time, timedelta
from typing import List, Tuple, Optional
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


@dataclass(frozen=True)
class ScheduledMatchSlot:
    """Estructura inmutable que representa la asignación espaciotemporal de un partido."""
    round_number: int
    round_date: date
    home_team_id: uuid.UUID
    away_team_id: uuid.UUID
    pitch_id: int
    start_time: time
    end_time: time


def generate_round_robin_pairings(team_ids: List[uuid.UUID]) -> List[List[Tuple[uuid.UUID, uuid.UUID]]]:
    """
    Algoritmo de Berger (Round-Robin canonical).
    Genera los emparejamientos para que cada equipo enfrente una sola vez a cada rival.
    Si el número de equipos es impar, agrega un comodín (fecha libre / bye).
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
        # Rotar todos los elementos excepto el primero (posición pivote)
        current_teams = [current_teams[0]] + [current_teams[-1]] + current_teams[1:-1]

    return rounds


def schedule_pairings_to_slots(
    pairings_by_round: List[List[Tuple[uuid.UUID, uuid.UUID]]],
    start_date: date,
    pitch_ids: List[int],
    match_slots: List[Tuple[time, time]] = MATCH_SLOTS,
    days_between_rounds: int = 7
) -> List[List[ScheduledMatchSlot]]:
    """
    Lógica pura de programación horaria y asignación de canchas.
    Distribuye los partidos de cada fecha de forma balanceada sobre las canchas disponibles
    y las franjas horarias reglamentarias.
    """
    if not pitch_ids:
        raise ValueError("Se requiere al menos una cancha disponible para programar partidos")
    if not match_slots:
        raise ValueError("Se requieren franjas horarias disponibles para programar partidos")

    scheduled_rounds: List[List[ScheduledMatchSlot]] = []
    num_pitches = len(pitch_ids)
    num_slots = len(match_slots)

    for round_idx, pairings in enumerate(pairings_by_round):
        round_number = round_idx + 1
        round_date = start_date + timedelta(days=round_idx * days_between_rounds)
        round_slots: List[ScheduledMatchSlot] = []

        for match_idx, (home_id, away_id) in enumerate(pairings):
            # Rotación uniforme de cancha y horario
            pitch_id = pitch_ids[match_idx % num_pitches]
            slot_idx = (match_idx // num_pitches) % num_slots
            start_t, end_t = match_slots[slot_idx]

            round_slots.append(
                ScheduledMatchSlot(
                    round_number=round_number,
                    round_date=round_date,
                    home_team_id=home_id,
                    away_team_id=away_id,
                    pitch_id=pitch_id,
                    start_time=start_t,
                    end_time=end_t
                )
            )

        scheduled_rounds.append(round_slots)

    return scheduled_rounds


class FixtureEngine:
    @staticmethod
    async def _validate_and_get_tournament(tournament_id: uuid.UUID, db: AsyncSession) -> Tournament:
        """Valida que el torneo exista y no tenga fixture generado previamente."""
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
        return tournament

    @staticmethod
    async def _ensure_tournament_pitches(db: AsyncSession) -> List[Pitch]:
        """Obtiene las canchas disponibles o inicializa las 4 canchas reglamentarias si no existen."""
        pitches_query = await db.execute(
            select(Pitch).where(Pitch.is_available == True).order_by(Pitch.pitch_number)
        )
        pitches = list(pitches_query.scalars().all())
        if not pitches:
            for i in range(1, 5):
                db.add(Pitch(id=i, name=f"Cancha {i}", pitch_number=i, is_available=True))
            await db.flush()
            pitches_query = await db.execute(
                select(Pitch).where(Pitch.is_available == True).order_by(Pitch.pitch_number)
            )
            pitches = list(pitches_query.scalars().all())
        return pitches

    @staticmethod
    async def _initialize_team_standings(tournament_id: uuid.UUID, teams: List[Team], db: AsyncSession) -> None:
        """Asegura que todos los equipos activos tengan una fila inicial en la tabla de posiciones."""
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

    @classmethod
    async def generate_fixture_for_tournament(
        cls,
        tournament_id: uuid.UUID,
        db: AsyncSession
    ) -> List[Round]:
        """
        Orquesta la generación y persistencia del fixture completo para un torneo.
        Garantiza: todos contra todos a 1 rueda, sin duplicados ni doble partido por fecha.
        """
        # 1. Validar torneo
        tournament = await cls._validate_and_get_tournament(tournament_id, db)

        # 2. Validar equipos participantes
        teams_query = await db.execute(
            select(Team).where(Team.tournament_id == tournament_id, Team.is_active == True)
        )
        teams = list(teams_query.scalars().all())
        if len(teams) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requieren al menos 2 equipos activos para generar el fixture"
            )

        # 3. Obtener canchas e inicializar tabla de posiciones
        pitches = await cls._ensure_tournament_pitches(db)
        await cls._initialize_team_standings(tournament_id, teams, db)

        # 4. Cálculo algorítmico puro (aislado y testeable)
        team_ids = [t.id for t in teams]
        pairings_by_round = generate_round_robin_pairings(team_ids)
        pitch_ids = [p.id for p in pitches]
        scheduled_rounds = schedule_pairings_to_slots(
            pairings_by_round=pairings_by_round,
            start_date=tournament.start_date,
            pitch_ids=pitch_ids,
            match_slots=MATCH_SLOTS
        )

        # 5. Persistencia en base de datos
        created_rounds: List[Round] = []
        for round_slots in scheduled_rounds:
            first_slot = round_slots[0]
            round_obj = Round(
                tournament_id=tournament_id,
                round_number=first_slot.round_number,
                name=f"Fecha {first_slot.round_number}",
                scheduled_date=first_slot.round_date,
                status="PENDIENTE"
            )
            db.add(round_obj)
            await db.flush()  # Generar ID de la ronda para las FKs de los partidos

            for slot in round_slots:
                match_obj = Match(
                    round_id=round_obj.id,
                    tournament_id=tournament_id,
                    home_team_id=slot.home_team_id,
                    away_team_id=slot.away_team_id,
                    pitch_id=slot.pitch_id,
                    match_date=slot.round_date,
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                    status="PENDIENTE",
                    is_locked=False
                )
                db.add(match_obj)

            created_rounds.append(round_obj)

        tournament.fixture_generated = True
        await db.commit()
        return created_rounds

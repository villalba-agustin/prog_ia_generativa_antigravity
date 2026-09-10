import uuid
from datetime import date, timedelta
from typing import Optional, Tuple
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.match import Match
from app.models.pitch import Pitch
from app.services.fixture_engine import MATCH_SLOTS


class RescheduleEngine:
    @staticmethod
    async def reschedule_match(
        match_id: uuid.UUID,
        db: AsyncSession,
        preferred_start_date: Optional[date] = None
    ) -> Match:
        # 1. Obtener partido
        match_query = await db.execute(select(Match).where(Match.id == match_id))
        match = match_query.scalar_one_or_none()
        if not match:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partido no encontrado")

        if match.status not in ["SUSPENDIDO", "CANCELADO"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Solo se pueden reprogramar partidos SUSPENDIDOS o CANCELADOS (estado actual: {match.status})"
            )

        # 2. Obtener canchas disponibles
        pitches_query = await db.execute(
            select(Pitch).where(Pitch.is_available == True).order_by(Pitch.pitch_number)
        )
        pitches = list(pitches_query.scalars().all())
        if not pitches:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No hay canchas disponibles")

        start_search_date = preferred_start_date or (match.match_date + timedelta(days=1))

        # 3. Buscar slot libre en los próximos 30 días
        found_slot: Optional[Tuple[date, Pitch, Tuple]] = None

        for day_offset in range(30):
            candidate_date = start_search_date + timedelta(days=day_offset)

            # Verificar si alguno de los dos equipos ya tiene partido programado en esa fecha
            team_conflict_query = await db.execute(
                select(Match).where(
                    Match.tournament_id == match.tournament_id,
                    Match.match_date == candidate_date,
                    Match.id != match.id,
                    Match.status != "CANCELADO",
                    or_(
                        Match.home_team_id == match.home_team_id,
                        Match.home_team_id == match.away_team_id,
                        Match.away_team_id == match.home_team_id,
                        Match.away_team_id == match.away_team_id
                    )
                )
            )
            if team_conflict_query.scalars().first():
                # Al menos un equipo ya juega en esta fecha -> continuar al siguiente día
                continue

            # Para cada slot y cada cancha, verificar disponibilidad
            for slot in MATCH_SLOTS:
                start_t, end_t = slot
                for pitch in pitches:
                    # Verificar si la cancha está ocupada en ese horario
                    pitch_busy_query = await db.execute(
                        select(Match).where(
                            Match.pitch_id == pitch.id,
                            Match.match_date == candidate_date,
                            Match.id != match.id,
                            Match.status != "CANCELADO",
                            and_(
                                Match.start_time < end_t,
                                Match.end_time > start_t
                            )
                        )
                    )
                    if not pitch_busy_query.scalars().first():
                        # ¡Slot encontrado!
                        found_slot = (candidate_date, pitch, slot)
                        break
                if found_slot:
                    break
            if found_slot:
                break

        if not found_slot:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se encontró ningún slot libre para reprogramar el partido en la ventana analizada"
            )

        new_date, new_pitch, (new_start_t, new_end_t) = found_slot

        # 4. Asignar nuevo slot y cambiar estado a PENDIENTE
        match.pitch_id = new_pitch.id
        match.match_date = new_date
        match.start_time = new_start_t
        match.end_time = new_end_t
        match.status = "PENDIENTE"
        match.is_locked = False
        match.home_score = None
        match.away_score = None

        await db.commit()
        await db.refresh(match)
        return match

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.match import Match
from app.models.player import Player
from app.models.stats import MatchStat
from app.schemas.match import MatchResultUpdate, MatchStatusUpdate
from app.schemas.stats import MatchStatCreate
from app.services.standings_engine import StandingsEngine


class MatchService:
    @staticmethod
    async def record_result(
        match_id: uuid.UUID,
        payload: MatchResultUpdate,
        db: AsyncSession
    ) -> Match:
        """
        Carga el resultado de un partido.
        REGLA DE NEGOCIO: Una vez cargado el resultado (o si el partido ya está JUGADO/is_locked),
        NO debe poder modificarse desde la aplicación.
        """
        match_query = await db.execute(select(Match).where(Match.id == match_id))
        match = match_query.scalar_one_or_none()
        if not match:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partido no encontrado")

        if match.status == "JUGADO" or match.is_locked:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Operación no permitida: El resultado de este partido ya fue registrado y es inmutable."
            )

        if match.status in ["SUSPENDIDO", "CANCELADO"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede registrar resultado para un partido con estado {match.status}. Debe ser reprogramado primero."
            )

        match.home_score = payload.home_score
        match.away_score = payload.away_score
        match.status = "JUGADO"
        match.is_locked = True
        match.played_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(match)

        # Recalcular automáticamente la tabla de posiciones
        await StandingsEngine.recalculate_tournament_standings(match.tournament_id, db)

        return match

    @staticmethod
    async def update_status(
        match_id: uuid.UUID,
        payload: MatchStatusUpdate,
        db: AsyncSession
    ) -> Match:
        match_query = await db.execute(select(Match).where(Match.id == match_id))
        match = match_query.scalar_one_or_none()
        if not match:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partido no encontrado")

        if match.is_locked or match.status == "JUGADO":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede cambiar el estado de un partido ya jugado."
            )

        target_status = payload.status.upper()
        if target_status not in ["SUSPENDIDO", "CANCELADO"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estado inválido. Debe ser SUSPENDIDO o CANCELADO"
            )

        match.status = target_status
        await db.commit()
        await db.refresh(match)
        return match

    @staticmethod
    async def record_player_stats(
        match_id: uuid.UUID,
        stats_list: List[MatchStatCreate],
        db: AsyncSession
    ) -> List[MatchStat]:
        """
        Registra estadísticas individuales de jugadores (goles, tarjetas amarillas, tarjetas rojas).
        Se permite cargar posteriormente a la carga del resultado.
        """
        match_query = await db.execute(select(Match).where(Match.id == match_id))
        match = match_query.scalar_one_or_none()
        if not match:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partido no encontrado")

        if match.status != "JUGADO":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Las estadísticas de jugadores solo pueden registrarse una vez que el partido esté JUGADO."
            )

        created_stats: List[MatchStat] = []
        for s in stats_list:
            # Validar que el jugador pertenezca a uno de los dos equipos
            player_query = await db.execute(select(Player).where(Player.id == s.player_id))
            player = player_query.scalar_one_or_none()
            if not player:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Jugador {s.player_id} no encontrado"
                )

            if player.team_id not in [match.home_team_id, match.away_team_id]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El jugador {player.first_name} {player.last_name} no pertenece a ninguno de los equipos participantes"
                )

            # Buscar si ya existe registro previo para este jugador en este partido
            existing_query = await db.execute(
                select(MatchStat).where(
                    MatchStat.match_id == match_id,
                    MatchStat.player_id == s.player_id
                )
            )
            existing_stat = existing_query.scalar_one_or_none()
            if existing_stat:
                existing_stat.goals = s.goals
                existing_stat.yellow_cards = s.yellow_cards
                existing_stat.red_cards = s.red_cards
                created_stats.append(existing_stat)
            else:
                stat_obj = MatchStat(
                    match_id=match_id,
                    team_id=player.team_id,
                    player_id=s.player_id,
                    goals=s.goals,
                    yellow_cards=s.yellow_cards,
                    red_cards=s.red_cards
                )
                db.add(stat_obj)
                created_stats.append(stat_obj)

        await db.commit()

        # Recalcular tabla de posiciones para actualizar Fair Play (tarjetas)
        await StandingsEngine.recalculate_tournament_standings(match.tournament_id, db)

        return created_stats

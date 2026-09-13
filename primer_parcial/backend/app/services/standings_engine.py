"""
Motor de cálculo y jerarquía de posiciones para Liga de Barrios y Fincas.
Implementa el reglamento oficial de puntuación y los criterios estrictos de desempate:
1. Puntos (PTS desc)
2. Diferencia de Gol (DG desc)
3. Goles a Favor (GF desc)
4. Enfrentamiento particular entre los empatados (Head-to-head desc)
5. Fair play (menos tarjetas / penalizaciones asc)
6. Criterio determinista
"""

import uuid
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team
from app.models.match import Match
from app.models.stats import MatchStat
from app.models.standings import Standing


class TeamStatsAccumulator:
    """Acumulador mutable de estadísticas de un equipo en un torneo."""
    def __init__(self, team_id: uuid.UUID):
        self.team_id = team_id
        self.played = 0
        self.won = 0
        self.drawn = 0
        self.lost = 0
        self.goals_for = 0
        self.goals_against = 0
        self.points = 0
        self.yellow_cards = 0
        self.red_cards = 0

    @property
    def goal_diff(self) -> int:
        return self.goals_for - self.goals_against

    @property
    def fair_play_score(self) -> int:
        """Puntaje de penalización: Amarilla = 1 pt, Roja = 3 pts."""
        return (self.yellow_cards * 1) + (self.red_cards * 3)

    def record_match_result(self, goals_scored: int, goals_conceded: int) -> None:
        """Registra el marcador de un partido jugado y actualiza puntos y balance."""
        self.played += 1
        self.goals_for += goals_scored
        self.goals_against += goals_conceded

        if goals_scored > goals_conceded:
            self.won += 1
            self.points += 3
        elif goals_scored < goals_conceded:
            self.lost += 1
        else:
            self.drawn += 1
            self.points += 1

    def record_disciplinary_cards(self, yellows: int, reds: int) -> None:
        """Acumula tarjetas disciplinarias."""
        self.yellow_cards += yellows
        self.red_cards += reds


@dataclass(frozen=True)
class CompletedMatchResult:
    """Representación inmutable de un partido jugado para cálculo de posiciones."""
    home_team_id: uuid.UUID
    away_team_id: uuid.UUID
    home_score: int
    away_score: int


def compute_head_to_head_record(
    team_id: uuid.UUID,
    tied_group_ids: Set[uuid.UUID],
    matches: List[CompletedMatchResult]
) -> Tuple[int, int, int]:
    """
    Calcula (puntos, dif_gol, goles_a_favor) de team_id exclusivamente
    en los partidos disputados contra rivales del grupo de empate (tied_group_ids).
    """
    h2h_pts = 0
    h2h_gf = 0
    h2h_ga = 0

    for m in matches:
        if m.home_team_id in tied_group_ids and m.away_team_id in tied_group_ids:
            if m.home_team_id == team_id:
                h2h_gf += m.home_score
                h2h_ga += m.away_score
                if m.home_score > m.away_score:
                    h2h_pts += 3
                elif m.home_score == m.away_score:
                    h2h_pts += 1
            elif m.away_team_id == team_id:
                h2h_gf += m.away_score
                h2h_ga += m.home_score
                if m.away_score > m.home_score:
                    h2h_pts += 3
                elif m.away_score == m.home_score:
                    h2h_pts += 1

    return (h2h_pts, h2h_gf - h2h_ga, h2h_gf)


def compute_standings_ranking(
    team_ids: List[uuid.UUID],
    played_matches: List[CompletedMatchResult],
    team_cards: Optional[Dict[uuid.UUID, Tuple[int, int]]] = None
) -> List[TeamStatsAccumulator]:
    """
    Función pura que procesa resultados y devuelve los acumuladores ordenados según
    la jerarquía oficial de desempates del torneo:
    1. Mayor cantidad de puntos (PTS)
    2. Mayor diferencia de goles (DG)
    3. Mayor cantidad de goles a favor (GF)
    4. Enfrentamiento particular entre empatados (Head-to-head)
    5. Menor puntaje de penalización por tarjetas (Fair Play)
    6. Criterio determinista
    """
    team_stats: Dict[uuid.UUID, TeamStatsAccumulator] = {
        tid: TeamStatsAccumulator(tid) for tid in team_ids
    }

    # 1. Procesar partidos
    for m in played_matches:
        if m.home_team_id in team_stats and m.away_team_id in team_stats:
            team_stats[m.home_team_id].record_match_result(m.home_score, m.away_score)
            team_stats[m.away_team_id].record_match_result(m.away_score, m.home_score)

    # 2. Asignar tarjetas Fair Play
    if team_cards:
        for tid, (yellows, reds) in team_cards.items():
            if tid in team_stats:
                team_stats[tid].record_disciplinary_cards(yellows, reds)

    # 3. Agrupar equipos por (Puntos, Dif. Gol, Goles Favor)
    all_accumulators = list(team_stats.values())
    groups: Dict[Tuple[int, int, int], List[TeamStatsAccumulator]] = {}
    for acc in all_accumulators:
        key = (acc.points, acc.goal_diff, acc.goals_for)
        groups.setdefault(key, []).append(acc)

    # 4. Ordenar grupos principales (PTS desc, DG desc, GF desc) y desempatar
    sorted_accumulators: List[TeamStatsAccumulator] = []
    for key in sorted(groups.keys(), key=lambda k: (-k[0], -k[1], -k[2])):
        group = groups[key]
        if len(group) == 1:
            sorted_accumulators.append(group[0])
        else:
            tied_ids = {item.team_id for item in group}

            def tiebreaker_key(item: TeamStatsAccumulator):
                h2h_pts, h2h_dg, h2h_gf = compute_head_to_head_record(item.team_id, tied_ids, played_matches)
                return (
                    -h2h_pts,              # Criterio 4a: Más puntos en Head-to-Head
                    -h2h_dg,               # Criterio 4b: Mayor dif. gol en Head-to-Head
                    -h2h_gf,               # Criterio 4c: Más goles a favor en Head-to-Head
                    item.fair_play_score,  # Criterio 5: Menor puntaje Fair Play (menos tarjetas)
                    str(item.team_id)      # Criterio 6: Determinista
                )

            sorted_group = sorted(group, key=tiebreaker_key)
            sorted_accumulators.extend(sorted_group)

    return sorted_accumulators


class StandingsEngine:
    @staticmethod
    def _sync_standing_record(standing: Standing, acc: TeamStatsAccumulator, position: int) -> None:
        """Sincroniza los campos de un modelo Standing a partir del acumulador."""
        standing.played = acc.played
        standing.won = acc.won
        standing.drawn = acc.drawn
        standing.lost = acc.lost
        standing.goals_for = acc.goals_for
        standing.goals_against = acc.goals_against
        standing.goal_diff = acc.goal_diff
        standing.points = acc.points
        standing.fair_play_score = acc.fair_play_score
        standing.position = position

    @classmethod
    async def recalculate_tournament_standings(
        cls,
        tournament_id: uuid.UUID,
        db: AsyncSession
    ) -> List[Standing]:
        """
        Recalcula y persiste la tabla de posiciones completa para un torneo activo.
        """
        # 1. Obtener equipos activos
        teams_query = await db.execute(
            select(Team).where(Team.tournament_id == tournament_id, Team.is_active == True)
        )
        teams = list(teams_query.scalars().all())
        if not teams:
            return []
        team_ids = [t.id for t in teams]

        # 2. Obtener partidos finalizados con marcador válido
        matches_query = await db.execute(
            select(Match).where(
                Match.tournament_id == tournament_id,
                Match.status == "JUGADO"
            )
        )
        completed_matches = [
            CompletedMatchResult(
                home_team_id=m.home_team_id,
                away_team_id=m.away_team_id,
                home_score=m.home_score,
                away_score=m.away_score
            )
            for m in matches_query.scalars().all()
            if m.home_score is not None and m.away_score is not None
        ]

        # 3. Obtener tarjetas acumuladas para Fair Play
        stats_query = await db.execute(
            select(MatchStat).join(Match, MatchStat.match_id == Match.id).where(
                Match.tournament_id == tournament_id
            )
        )
        team_cards: Dict[uuid.UUID, Tuple[int, int]] = {}
        for stat in stats_query.scalars().all():
            y, r = team_cards.get(stat.team_id, (0, 0))
            team_cards[stat.team_id] = (y + stat.yellow_cards, r + stat.red_cards)

        # 4. Cálculo puro desacoplado de la base de datos
        ranked_accumulators = compute_standings_ranking(
            team_ids=team_ids,
            played_matches=completed_matches,
            team_cards=team_cards
        )

        # 5. Persistencia y sincronización en PostgreSQL
        existing_standings_query = await db.execute(
            select(Standing).where(Standing.tournament_id == tournament_id)
        )
        existing_map = {s.team_id: s for s in existing_standings_query.scalars().all()}

        result_standings: List[Standing] = []
        for position, acc in enumerate(ranked_accumulators, start=1):
            if acc.team_id in existing_map:
                standing = existing_map[acc.team_id]
            else:
                standing = Standing(tournament_id=tournament_id, team_id=acc.team_id)
                db.add(standing)

            cls._sync_standing_record(standing, acc, position)
            result_standings.append(standing)

        await db.commit()
        return result_standings

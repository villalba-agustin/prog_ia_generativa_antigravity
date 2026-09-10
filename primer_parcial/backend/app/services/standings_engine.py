import uuid
from typing import List, Dict, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team
from app.models.match import Match
from app.models.stats import MatchStat
from app.models.standings import Standing


class TeamStatsAccumulator:
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
        # Amarilla = 1 pt de penalización, Roja = 3 pts de penalización
        return (self.yellow_cards * 1) + (self.red_cards * 3)


class StandingsEngine:
    @staticmethod
    async def recalculate_tournament_standings(
        tournament_id: uuid.UUID,
        db: AsyncSession
    ) -> List[Standing]:
        """
        Recalcula la tabla de posiciones completa para un torneo a partir de los partidos con estado JUGADO.
        Aplica los 5 criterios de desempate en orden:
        1. Puntos (PTS desc)
        2. Diferencia de Gol (DG desc)
        3. Goles a Favor (GF desc)
        4. Enfrentamiento particular entre los empatados (Head-to-head)
        5. Menos tarjetas (Fair play asc)
        6. Sorteo / Criterio determinista
        """
        # 1. Obtener todos los equipos activos del torneo
        teams_query = await db.execute(
            select(Team).where(Team.tournament_id == tournament_id, Team.is_active == True)
        )
        teams = list(teams_query.scalars().all())
        if not teams:
            return []

        team_stats: Dict[uuid.UUID, TeamStatsAccumulator] = {
            t.id: TeamStatsAccumulator(t.id) for t in teams
        }

        # 2. Obtener partidos JUGADOS
        matches_query = await db.execute(
            select(Match).where(
                Match.tournament_id == tournament_id,
                Match.status == "JUGADO"
            )
        )
        played_matches = list(matches_query.scalars().all())

        # Acumular estadísticas de partidos
        for m in played_matches:
            if m.home_score is None or m.away_score is None:
                continue

            if m.home_team_id in team_stats and m.away_team_id in team_stats:
                h = team_stats[m.home_team_id]
                a = team_stats[m.away_team_id]

                h.played += 1
                a.played += 1
                h.goals_for += m.home_score
                h.goals_against += m.away_score
                a.goals_for += m.away_score
                a.goals_against += m.home_score

                if m.home_score > m.away_score:
                    h.won += 1
                    h.points += 3
                    a.lost += 1
                elif m.home_score < m.away_score:
                    a.won += 1
                    a.points += 3
                    h.lost += 1
                else:
                    h.drawn += 1
                    a.drawn += 1
                    h.points += 1
                    a.points += 1

        # 3. Obtener tarjetas para Fair Play
        stats_query = await db.execute(
            select(MatchStat).join(Match, MatchStat.match_id == Match.id).where(
                Match.tournament_id == tournament_id
            )
        )
        for stat in stats_query.scalars().all():
            if stat.team_id in team_stats:
                team_stats[stat.team_id].yellow_cards += stat.yellow_cards
                team_stats[stat.team_id].red_cards += stat.red_cards

        # 4. Desempate particular: Función para Head-to-Head entre un subconjunto de equipos empatados
        def head_to_head_score(team_id: uuid.UUID, tied_group_ids: set) -> Tuple[int, int, int]:
            """
            Calcula (puntos, dif_gol, goles_favor) de team_id en los partidos jugados exclusivamente contra los rivales de tied_group_ids.
            """
            h2h_pts = 0
            h2h_gf = 0
            h2h_ga = 0
            for m in played_matches:
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

        # 5. Agrupar por (PTS, DG, GF) para aplicar Head-to-Head solo a los empatados
        all_accumulators = list(team_stats.values())
        groups: Dict[Tuple[int, int, int], List[TeamStatsAccumulator]] = {}
        for acc in all_accumulators:
            key = (acc.points, acc.goal_diff, acc.goals_for)
            groups.setdefault(key, []).append(acc)

        sorted_accumulators: List[TeamStatsAccumulator] = []

        # Ordenar los grupos principales por (PTS desc, DG desc, GF desc)
        for key in sorted(groups.keys(), key=lambda k: (-k[0], -k[1], -k[2])):
            group = groups[key]
            if len(group) == 1:
                sorted_accumulators.append(group[0])
            else:
                # Más de 1 equipo empatado en PTS, DG y GF -> Aplicar Criterio 3 (H2H), Criterio 4 (Fair Play), Criterio 5 (Sorteo)
                tied_ids = {item.team_id for item in group}
                
                def tied_comparator(item: TeamStatsAccumulator):
                    h2h_pts, h2h_dg, h2h_gf = head_to_head_score(item.team_id, tied_ids)
                    return (
                        -h2h_pts,                # Criterio 3: Más puntos entre sí
                        -h2h_dg,                 # Criterio 3b: Más dif gol entre sí
                        -h2h_gf,                 # Criterio 3c: Más goles entre sí
                        item.fair_play_score,    # Criterio 4: Menos tarjetas (Fair Play)
                        str(item.team_id)        # Criterio 5: Sorteo / Determinista
                    )

                sorted_group = sorted(group, key=tied_comparator)
                sorted_accumulators.extend(sorted_group)

        # 6. Guardar / Actualizar en la base de datos
        existing_standings_query = await db.execute(
            select(Standing).where(Standing.tournament_id == tournament_id)
        )
        existing_standings = {s.team_id: s for s in existing_standings_query.scalars().all()}

        result_standings: List[Standing] = []
        for pos_idx, acc in enumerate(sorted_accumulators, start=1):
            if acc.team_id in existing_standings:
                standing = existing_standings[acc.team_id]
                standing.played = acc.played
                standing.won = acc.won
                standing.drawn = acc.drawn
                standing.lost = acc.lost
                standing.goals_for = acc.goals_for
                standing.goals_against = acc.goals_against
                standing.goal_diff = acc.goal_diff
                standing.points = acc.points
                standing.fair_play_score = acc.fair_play_score
                standing.position = pos_idx
            else:
                standing = Standing(
                    tournament_id=tournament_id,
                    team_id=acc.team_id,
                    played=acc.played,
                    won=acc.won,
                    drawn=acc.drawn,
                    lost=acc.lost,
                    goals_for=acc.goals_for,
                    goals_against=acc.goals_against,
                    goal_diff=acc.goal_diff,
                    points=acc.points,
                    fair_play_score=acc.fair_play_score,
                    position=pos_idx
                )
                db.add(standing)
            result_standings.append(standing)

        await db.commit()
        return result_standings

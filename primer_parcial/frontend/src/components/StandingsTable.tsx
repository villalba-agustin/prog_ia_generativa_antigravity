import React from 'react';
import { Standing } from '../types';
import { Trophy, HelpCircle } from 'lucide-react';

interface StandingsTableProps {
  standings: Standing[];
  loading?: boolean;
}

export const StandingsTable: React.FC<StandingsTableProps> = ({ standings, loading }) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-emerald-400 font-medium">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mr-3"></div>
        Cargando tabla de posiciones...
      </div>
    );
  }

  if (!standings || standings.length === 0) {
    return (
      <div className="p-12 text-center text-slate-400 glass-card rounded-2xl">
        <Trophy className="w-12 h-12 mx-auto mb-3 text-slate-600" />
        <h3 className="text-lg font-bold text-slate-300">Aún no hay posiciones registradas</h3>
        <p className="text-sm text-slate-500 mt-1">La tabla se actualizará automáticamente cuando comiencen a disputarse los partidos.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2">
        <div>
          <h2 className="text-xl sm:text-2xl font-heading font-bold text-white flex items-center gap-2">
            <Trophy className="w-6 h-6 text-yellow-400" />
            Tabla de Posiciones
          </h2>
          <p className="text-xs sm:text-sm text-slate-400">
            Formato: Todos contra todos a 1 rueda. Victoria = 3 pts, Empate = 1 pt, Derrota = 0 pts.
          </p>
        </div>
      </div>

      {/* Table Card */}
      <div className="glass-card rounded-2xl overflow-hidden border border-slate-800 shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-slate-900/90 text-slate-400 text-xs uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-3 text-center w-12">#</th>
                <th className="py-3.5 px-4">Equipo</th>
                <th className="py-3.5 px-3 text-center" title="Partidos Jugados">PJ</th>
                <th className="py-3.5 px-3 text-center" title="Partidos Ganados">PG</th>
                <th className="py-3.5 px-3 text-center" title="Partidos Empatados">PE</th>
                <th className="py-3.5 px-3 text-center" title="Partidos Perdidos">PP</th>
                <th className="py-3.5 px-3 text-center" title="Goles a Favor">GF</th>
                <th className="py-3.5 px-3 text-center" title="Goles en Contra">GC</th>
                <th className="py-3.5 px-3 text-center font-bold" title="Diferencia de Gol">DG</th>
                <th className="py-3.5 px-4 text-center font-extrabold text-emerald-400 bg-emerald-950/20" title="Puntos">PTS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {standings.map((team, idx) => {
                const isLeader = team.position === 1;
                const isPodium = team.position <= 3;
                return (
                  <tr
                    key={team.team_id}
                    className={`hover:bg-slate-800/40 transition-colors ${
                      isLeader ? 'bg-emerald-950/20' : idx % 2 === 0 ? 'bg-slate-900/30' : ''
                    }`}
                  >
                    {/* Position */}
                    <td className="py-3.5 px-3 text-center">
                      <span
                        className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                          isLeader
                            ? 'bg-yellow-400 text-slate-950 shadow-sm shadow-yellow-400/50'
                            : team.position === 2
                            ? 'bg-slate-300 text-slate-900'
                            : team.position === 3
                            ? 'bg-amber-600 text-white'
                            : 'text-slate-400'
                        }`}
                      >
                        {team.position}
                      </span>
                    </td>

                    {/* Team Name */}
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-slate-300 shrink-0">
                          {team.team_short_name.slice(0, 3)}
                        </div>
                        <div>
                          <div className="font-bold text-slate-100 flex items-center gap-1.5">
                            {team.team_name}
                            {isLeader && (
                              <span className="text-[10px] bg-yellow-500/20 text-yellow-300 border border-yellow-500/30 px-1.5 py-0.2 rounded font-semibold uppercase">
                                Puntero
                              </span>
                            )}
                          </div>
                          <span className="text-xs text-slate-500 sm:hidden">
                            {team.team_short_name}
                          </span>
                        </div>
                      </div>
                    </td>

                    {/* Stats */}
                    <td className="py-3.5 px-3 text-center text-slate-300">{team.played}</td>
                    <td className="py-3.5 px-3 text-center text-emerald-400">{team.won}</td>
                    <td className="py-3.5 px-3 text-center text-slate-400">{team.drawn}</td>
                    <td className="py-3.5 px-3 text-center text-rose-400">{team.lost}</td>
                    <td className="py-3.5 px-3 text-center text-slate-300">{team.goals_for}</td>
                    <td className="py-3.5 px-3 text-center text-slate-400">{team.goals_against}</td>
                    <td className={`py-3.5 px-3 text-center font-bold ${
                      team.goal_diff > 0 ? 'text-emerald-400' : team.goal_diff < 0 ? 'text-rose-400' : 'text-slate-400'
                    }`}>
                      {team.goal_diff > 0 ? `+${team.goal_diff}` : team.goal_diff}
                    </td>

                    {/* Points */}
                    <td className="py-3.5 px-4 text-center font-extrabold text-base text-emerald-300 bg-emerald-950/30">
                      {team.points}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Tiebreaker Rules Guide Footnote */}
      <div className="p-4 rounded-xl glass border border-slate-800/80 text-xs text-slate-400 space-y-1.5">
        <div className="font-semibold text-slate-300 flex items-center gap-1.5">
          <HelpCircle className="w-4 h-4 text-emerald-400" />
          Criterios oficiales de desempate en la tabla (Reglamento del Torneo):
        </div>
        <ol className="list-decimal list-inside space-y-0.5 text-slate-400 pl-1">
          <li>Mayor <strong className="text-slate-300">Diferencia de Gol (DG)</strong></li>
          <li>Mayor cantidad de <strong className="text-slate-300">Goles a Favor (GF)</strong></li>
          <li><strong className="text-slate-300">Resultado entre ambos (Head-to-head)</strong> en los partidos jugados entre los equipos empatados</li>
          <li><strong className="text-slate-300">Menos tarjetas (Fair Play)</strong>: 1 pt por amarilla, 3 pts por roja directa</li>
          <li><strong className="text-slate-300">Sorteo</strong></li>
        </ol>
      </div>
    </div>
  );
};

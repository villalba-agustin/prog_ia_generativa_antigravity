import React from 'react';
import { FairPlay } from '../types';
import { AlertTriangle, Shield } from 'lucide-react';

interface FairPlayViewProps {
  fairPlayList: FairPlay[];
  loading?: boolean;
}

export const FairPlayView: React.FC<FairPlayViewProps> = ({ fairPlayList, loading }) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-emerald-400 font-medium">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mr-3"></div>
        Cargando ranking de conducta...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl sm:text-2xl font-heading font-bold text-white flex items-center gap-2">
          <AlertTriangle className="w-6 h-6 text-amber-400" />
          Ranking de Fair Play (Conducta Deportiva)
        </h2>
        <p className="text-xs sm:text-sm text-slate-400">
          Penalización: 1 pt por Tarjeta Amarilla, 3 pts por Tarjeta Roja. (Menor puntaje = Mejor conducta).
        </p>
      </div>

      <div className="glass-card rounded-2xl overflow-hidden border border-slate-800 shadow-xl">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-slate-900/90 text-slate-400 text-xs uppercase tracking-wider font-semibold border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 text-center w-12">#</th>
              <th className="py-3 px-4">Equipo</th>
              <th className="py-3 px-4 text-center">
                <span className="inline-flex items-center gap-1 text-yellow-400">
                  <span className="w-2.5 h-3.5 bg-yellow-400 rounded-xs inline-block"></span>
                  Amarillas
                </span>
              </th>
              <th className="py-3 px-4 text-center">
                <span className="inline-flex items-center gap-1 text-rose-400">
                  <span className="w-2.5 h-3.5 bg-rose-500 rounded-xs inline-block"></span>
                  Rojas
                </span>
              </th>
              <th className="py-3 px-6 text-center font-bold text-emerald-400">Puntaje Fair Play</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-medium">
            {fairPlayList.map((team, idx) => (
              <tr key={team.team_id} className="hover:bg-slate-800/40 transition-colors">
                <td className="py-3 px-4 text-center text-slate-400">
                  {idx + 1}
                </td>
                <td className="py-3 px-4 font-bold text-slate-100 flex items-center gap-2">
                  <Shield className="w-4 h-4 text-slate-500" />
                  {team.team_name}
                </td>
                <td className="py-3 px-4 text-center text-yellow-300 font-bold">
                  {team.yellow_cards}
                </td>
                <td className="py-3 px-4 text-center text-rose-400 font-bold">
                  {team.red_cards}
                </td>
                <td className="py-3 px-6 text-center font-extrabold text-base text-slate-200">
                  {team.fair_play_score} pts
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

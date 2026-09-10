import React from 'react';
import { TopScorer } from '../types';
import { Users, Award, Shield } from 'lucide-react';

interface ScorersViewProps {
  scorers: TopScorer[];
  loading?: boolean;
}

export const ScorersView: React.FC<ScorersViewProps> = ({ scorers, loading }) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-emerald-400 font-medium">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mr-3"></div>
        Cargando tabla de goleadores...
      </div>
    );
  }

  if (!scorers || scorers.length === 0) {
    return (
      <div className="p-12 text-center text-slate-400 glass-card rounded-2xl">
        <Users className="w-12 h-12 mx-auto mb-3 text-slate-600" />
        <h3 className="text-lg font-bold text-slate-300">Aún no hay goles registrados</h3>
        <p className="text-sm text-slate-500 mt-1">Los goleadores se registrarán a medida que se carguen las estadísticas de los partidos.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl sm:text-2xl font-heading font-bold text-white flex items-center gap-2">
          <Award className="w-6 h-6 text-yellow-400" />
          Tabla de Goleadores
        </h2>
        <p className="text-xs sm:text-sm text-slate-400">
          Máximos artilleros del Torneo Apertura 2026
        </p>
      </div>

      <div className="glass-card rounded-2xl overflow-hidden border border-slate-800 shadow-xl">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-slate-900/90 text-slate-400 text-xs uppercase tracking-wider font-semibold border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 text-center w-12">#</th>
              <th className="py-3 px-4">Jugador</th>
              <th className="py-3 px-4">Equipo</th>
              <th className="py-3 px-4 text-center">Camiseta</th>
              <th className="py-3 px-6 text-center font-bold text-yellow-400">Goles</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-medium">
            {scorers.map((scorer, idx) => (
              <tr key={scorer.player_id} className="hover:bg-slate-800/40 transition-colors">
                <td className="py-3 px-4 text-center">
                  <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                    idx === 0 ? 'bg-yellow-400 text-slate-950 font-extrabold' : 'text-slate-400'
                  }`}>
                    {idx + 1}
                  </span>
                </td>
                <td className="py-3 px-4 font-bold text-slate-100">
                  {scorer.player_name}
                </td>
                <td className="py-3 px-4 text-slate-400 flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-emerald-400" />
                  {scorer.team_name}
                </td>
                <td className="py-3 px-4 text-center">
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-xs border border-slate-700">
                    #{scorer.jersey_number}
                  </span>
                </td>
                <td className="py-3 px-6 text-center font-black text-base text-yellow-400">
                  {scorer.goals}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

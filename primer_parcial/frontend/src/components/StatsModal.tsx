import React, { useState, useEffect } from 'react';
import { Match, Player } from '../types';
import { api } from '../api';
import { X, Check, BarChart3, AlertCircle, Award } from 'lucide-react';

interface StatsModalProps {
  match: Match | null;
  onClose: () => void;
  onSuccess: () => void;
}

interface PlayerStatRow {
  player: Player;
  team_id: string;
  team_name: string;
  goals: number;
  yellow_cards: number;
  red_cards: number;
}

export const StatsModal: React.FC<StatsModalProps> = ({ match, onClose, onSuccess }) => {
  const [statsRows, setStatsRows] = useState<PlayerStatRow[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!match) return;

    const loadData = async () => {
      setLoading(true);
      try {
        const [homePlayers, awayPlayers, existingStats] = await Promise.all([
          api.getTeamPlayers(match.home_team_id),
          api.getTeamPlayers(match.away_team_id),
          api.getMatchStats(match.id)
        ]);

        const statsMap = new Map(existingStats.map(s => [s.player_id, s]));

        const combined: PlayerStatRow[] = [
          ...homePlayers.map(p => ({
            player: p,
            team_id: match.home_team_id,
            team_name: match.home_team?.name || 'Local',
            goals: statsMap.get(p.id)?.goals || 0,
            yellow_cards: statsMap.get(p.id)?.yellow_cards || 0,
            red_cards: statsMap.get(p.id)?.red_cards || 0,
          })),
          ...awayPlayers.map(p => ({
            player: p,
            team_id: match.away_team_id,
            team_name: match.away_team?.name || 'Visitante',
            goals: statsMap.get(p.id)?.goals || 0,
            yellow_cards: statsMap.get(p.id)?.yellow_cards || 0,
            red_cards: statsMap.get(p.id)?.red_cards || 0,
          }))
        ];

        setStatsRows(combined);
      } catch (err: any) {
        setError(err.message || 'Error al cargar plantel');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [match]);

  if (!match) return null;

  const handleStatChange = (playerId: string, field: 'goals' | 'yellow_cards' | 'red_cards', delta: number) => {
    setStatsRows(prev => prev.map(row => {
      if (row.player.id === playerId) {
        const val = row[field] + delta;
        let maxVal = 20;
        if (field === 'yellow_cards') maxVal = 2;
        if (field === 'red_cards') maxVal = 1;
        return { ...row, [field]: Math.max(0, Math.min(maxVal, val)) };
      }
      return row;
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const payload = statsRows
        .filter(r => r.goals > 0 || r.yellow_cards > 0 || r.red_cards > 0)
        .map(r => ({
          player_id: r.player.id,
          team_id: r.team_id,
          goals: r.goals,
          yellow_cards: r.yellow_cards,
          red_cards: r.red_cards
        }));

      await api.recordMatchStats(match.id, payload);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Error al guardar estadísticas');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="glass-card rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col p-6 border border-slate-700 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg bg-slate-800"
        >
          <X className="w-5 h-5" />
        </button>

        <div>
          <h3 className="text-xl font-heading font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-yellow-400" />
            Estadísticas Individuales del Partido
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            {match.home_team?.name} ({match.home_score}) vs {match.away_team?.name} ({match.away_score})
          </p>
        </div>

        {error && (
          <div className="mt-3 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            {error}
          </div>
        )}

        {loading ? (
          <div className="py-16 text-center text-emerald-400 font-medium">
            Cargando nómina de jugadores...
          </div>
        ) : (
          <div className="mt-4 overflow-y-auto flex-1 pr-1 space-y-4 scrollbar-thin">
            <table className="w-full text-left text-xs whitespace-nowrap">
              <thead className="bg-slate-900 sticky top-0 text-slate-400 uppercase font-semibold">
                <tr>
                  <th className="py-2.5 px-3">Jugador</th>
                  <th className="py-2.5 px-3">Equipo</th>
                  <th className="py-2.5 px-3 text-center">Goles</th>
                  <th className="py-2.5 px-3 text-center">Amarillas</th>
                  <th className="py-2.5 px-3 text-center">Rojas</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-medium">
                {statsRows.map(row => (
                  <tr key={row.player.id} className="hover:bg-slate-850">
                    <td className="py-2 px-3">
                      <div className="flex items-center gap-1.5">
                        <span className="w-5 h-5 rounded bg-slate-800 text-slate-300 font-mono text-[10px] flex items-center justify-center">
                          #{row.player.jersey_number}
                        </span>
                        <span className="text-slate-100 font-semibold">
                          {row.player.first_name} {row.player.last_name}
                        </span>
                      </div>
                    </td>
                    <td className="py-2 px-3 text-slate-400">
                      {row.team_name}
                    </td>

                    {/* Goals Controller */}
                    <td className="py-2 px-3 text-center">
                      <div className="inline-flex items-center gap-1.5 bg-slate-900 border border-slate-700 rounded-lg px-2 py-0.5">
                        <button
                          onClick={() => handleStatChange(row.player.id, 'goals', -1)}
                          className="text-slate-400 hover:text-white font-bold"
                        >-</button>
                        <span className="font-bold font-mono text-yellow-400 w-4 text-center">{row.goals}</span>
                        <button
                          onClick={() => handleStatChange(row.player.id, 'goals', 1)}
                          className="text-slate-400 hover:text-white font-bold"
                        >+</button>
                      </div>
                    </td>

                    {/* Yellow Cards Controller */}
                    <td className="py-2 px-3 text-center">
                      <div className="inline-flex items-center gap-1.5 bg-slate-900 border border-slate-700 rounded-lg px-2 py-0.5">
                        <button
                          onClick={() => handleStatChange(row.player.id, 'yellow_cards', -1)}
                          className="text-slate-400 hover:text-white font-bold"
                        >-</button>
                        <span className="font-bold font-mono text-yellow-300 w-4 text-center">{row.yellow_cards}</span>
                        <button
                          onClick={() => handleStatChange(row.player.id, 'yellow_cards', 1)}
                          className="text-slate-400 hover:text-white font-bold"
                        >+</button>
                      </div>
                    </td>

                    {/* Red Cards Controller */}
                    <td className="py-2 px-3 text-center">
                      <div className="inline-flex items-center gap-1.5 bg-slate-900 border border-slate-700 rounded-lg px-2 py-0.5">
                        <button
                          onClick={() => handleStatChange(row.player.id, 'red_cards', -1)}
                          className="text-slate-400 hover:text-white font-bold"
                        >-</button>
                        <span className="font-bold font-mono text-rose-400 w-4 text-center">{row.red_cards}</span>
                        <button
                          onClick={() => handleStatChange(row.player.id, 'red_cards', 1)}
                          className="text-slate-400 hover:text-white font-bold"
                        >+</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="mt-4 pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-sm font-medium text-slate-400 hover:text-white bg-slate-900"
          >
            Cerrar
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving || loading}
            className="px-5 py-2 rounded-xl text-sm font-bold text-white bg-emerald-600 hover:bg-emerald-500 shadow-md shadow-emerald-700/30 flex items-center gap-1.5 disabled:opacity-50"
          >
            <Check className="w-4 h-4" />
            {saving ? 'Guardando...' : 'Guardar Estadísticas'}
          </button>
        </div>
      </div>
    </div>
  );
};

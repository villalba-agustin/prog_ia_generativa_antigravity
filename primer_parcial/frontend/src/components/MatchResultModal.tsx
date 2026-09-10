import React, { useState } from 'react';
import { Match } from '../types';
import { api } from '../api';
import { AlertCircle, Check, X, ShieldAlert } from 'lucide-react';

interface MatchResultModalProps {
  match: Match | null;
  onClose: () => void;
  onSuccess: () => void;
}

export const MatchResultModal: React.FC<MatchResultModalProps> = ({ match, onClose, onSuccess }) => {
  const [homeScore, setHomeScore] = useState<number>(0);
  const [awayScore, setAwayScore] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!match) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (homeScore < 0 || awayScore < 0) {
      setError('Los goles no pueden ser negativos');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await api.recordResult(match.id, homeScore, awayScore);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Error al registrar el resultado');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="glass-card rounded-2xl w-full max-w-md p-6 border border-slate-700 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg bg-slate-800"
        >
          <X className="w-5 h-5" />
        </button>

        <h3 className="text-xl font-heading font-bold text-white mb-1">
          Cargar Resultado Oficial
        </h3>
        <p className="text-xs text-slate-400 mb-4">
          {match.pitch?.name} • Horario {match.start_time.slice(0, 5)} a {match.end_time.slice(0, 5)} (70')
        </p>

        {/* Immutability Notice Alert */}
        <div className="p-3 mb-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-start gap-2.5">
          <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <strong className="block font-semibold">Regla de Inmutabilidad:</strong>
            Una vez cargado el resultado, el partido pasará a estado <strong>JUGADO</strong> y <strong>NO podrá ser modificado</strong> desde la aplicación.
          </div>
        </div>

        {error && (
          <div className="p-3 mb-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-5 items-center gap-3 py-2">
            {/* Home Team */}
            <div className="col-span-2 text-center">
              <label className="block text-xs font-bold text-slate-300 mb-2 truncate">
                {match.home_team?.name}
              </label>
              <input
                type="number"
                min="0"
                max="30"
                value={homeScore}
                onChange={(e) => setHomeScore(Math.max(0, parseInt(e.target.value) || 0))}
                className="w-20 mx-auto text-center text-3xl font-black font-mono rounded-xl bg-slate-900 border-2 border-slate-700 text-white focus:border-emerald-500 focus:outline-none py-2"
              />
              <span className="block text-[11px] text-emerald-400 mt-1 font-mono">
                {match.home_team?.short_name} (Local)
              </span>
            </div>

            {/* VS Divider */}
            <div className="col-span-1 text-center font-bold text-slate-500 text-sm">
              VS
            </div>

            {/* Away Team */}
            <div className="col-span-2 text-center">
              <label className="block text-xs font-bold text-slate-300 mb-2 truncate">
                {match.away_team?.name}
              </label>
              <input
                type="number"
                min="0"
                max="30"
                value={awayScore}
                onChange={(e) => setAwayScore(Math.max(0, parseInt(e.target.value) || 0))}
                className="w-20 mx-auto text-center text-3xl font-black font-mono rounded-xl bg-slate-900 border-2 border-slate-700 text-white focus:border-emerald-500 focus:outline-none py-2"
              />
              <span className="block text-[11px] text-emerald-400 mt-1 font-mono">
                {match.away_team?.short_name} (Visitante)
              </span>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-sm font-medium text-slate-400 hover:text-white bg-slate-900 hover:bg-slate-800"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 rounded-xl text-sm font-bold text-white bg-emerald-600 hover:bg-emerald-500 shadow-lg shadow-emerald-700/30 flex items-center gap-1.5 transition-all disabled:opacity-50"
            >
              {loading ? 'Guardando...' : (
                <>
                  <Check className="w-4 h-4" />
                  Confirmar Resultado Inmutable
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

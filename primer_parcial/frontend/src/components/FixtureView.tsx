import React, { useState } from 'react';
import { RoundWithMatches, Match, User } from '../types';
import { Calendar, Clock, MapPin, CheckCircle, AlertCircle, RefreshCw, PlusCircle, BarChart3, AlertTriangle } from 'lucide-react';

interface FixtureViewProps {
  fixture: RoundWithMatches[];
  currentUser: User | null;
  onOpenResultModal: (match: Match) => void;
  onOpenStatsModal: (match: Match) => void;
  onRescheduleMatch: (match: Match) => void;
  onUpdateStatus: (match: Match, status: 'SUSPENDIDO' | 'CANCELADO') => void;
  loading?: boolean;
}

export const FixtureView: React.FC<FixtureViewProps> = ({
  fixture,
  currentUser,
  onOpenResultModal,
  onOpenStatsModal,
  onRescheduleMatch,
  onUpdateStatus,
  loading
}) => {
  const [selectedRoundIndex, setSelectedRoundIndex] = useState<number>(0);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-emerald-400 font-medium">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mr-3"></div>
        Cargando fixture...
      </div>
    );
  }

  if (!fixture || fixture.length === 0) {
    return (
      <div className="p-12 text-center text-slate-400 glass-card rounded-2xl">
        <Calendar className="w-12 h-12 mx-auto mb-3 text-slate-600" />
        <h3 className="text-lg font-bold text-slate-300">Fixture no generado</h3>
        <p className="text-sm text-slate-500 mt-1">
          El administrador debe generar el fixture oficial desde el panel de control.
        </p>
      </div>
    );
  }

  const currentRoundData = fixture[selectedRoundIndex] || fixture[0];
  const isAdmin = currentUser?.role === 'ADMINISTRADOR';

  return (
    <div className="space-y-6">
      {/* Title & Info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2">
        <div>
          <h2 className="text-xl sm:text-2xl font-heading font-bold text-white flex items-center gap-2">
            <Calendar className="w-6 h-6 text-emerald-400" />
            Fixture & Calendario Oficial
          </h2>
          <p className="text-xs sm:text-sm text-slate-400">
            4 canchas simultáneas • Duración: 70 min (30' PT + 10' ET + 30' ST) • Franja: 11:00 a 18:00
          </p>
        </div>
      </div>

      {/* Horizontal Round Selector Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-thin">
        {fixture.map((r, idx) => {
          const isSelected = idx === selectedRoundIndex;
          const totalMatches = r.matches.length;
          const playedCount = r.matches.filter(m => m.status === 'JUGADO').length;
          const isFinished = totalMatches > 0 && playedCount === totalMatches;

          return (
            <button
              key={r.round.id}
              onClick={() => setSelectedRoundIndex(idx)}
              className={`flex flex-col items-center px-4 py-2.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all border shrink-0 ${
                isSelected
                  ? 'bg-emerald-600 text-white border-emerald-500 shadow-lg shadow-emerald-700/20'
                  : 'glass text-slate-400 hover:text-slate-200 border-slate-800'
              }`}
            >
              <span>{r.round.name}</span>
              <span className={`text-[10px] mt-0.5 ${isSelected ? 'text-emerald-100' : 'text-slate-500'}`}>
                {isFinished ? '✓ Finalizada' : `${playedCount}/${totalMatches} jugados`}
              </span>
            </button>
          );
        })}
      </div>

      {/* Selected Round Info Header */}
      <div className="flex items-center justify-between px-4 py-2.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400">
        <span className="font-bold text-slate-200">
          {currentRoundData.round.name}
        </span>
        <span>
          Fecha programada: <strong className="text-slate-300">{currentRoundData.round.scheduled_date}</strong>
        </span>
      </div>

      {/* Matches Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {currentRoundData.matches.map((match) => {
          const isPlayed = match.status === 'JUGADO';
          const isPending = match.status === 'PENDIENTE';
          const isSuspended = match.status === 'SUSPENDIDO';
          const isCancelled = match.status === 'CANCELADO';

          return (
            <div
              key={match.id}
              className={`glass-card rounded-2xl p-4 border transition-all flex flex-col justify-between ${
                isPlayed
                  ? 'border-emerald-500/20'
                  : isSuspended || isCancelled
                  ? 'border-amber-500/30 bg-amber-950/10'
                  : 'border-slate-800 hover:border-slate-700'
              }`}
            >
              {/* Card Header: Pitch, Time, Status */}
              <div className="flex items-center justify-between text-xs text-slate-400 pb-3 border-b border-slate-800/60">
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1 font-semibold text-slate-300">
                    <MapPin className="w-3.5 h-3.5 text-emerald-400" />
                    {match.pitch?.name || `Cancha ${match.pitch_id}`}
                  </span>
                  <span className="flex items-center gap-1 text-slate-400">
                    <Clock className="w-3.5 h-3.5 text-slate-500" />
                    {match.start_time.slice(0, 5)} - {match.end_time.slice(0, 5)}
                    <span className="text-[10px] text-slate-500 font-mono">(70')</span>
                  </span>
                </div>

                <div>
                  {isPlayed && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      <CheckCircle className="w-3 h-3" /> JUGADO
                    </span>
                  )}
                  {isPending && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                      PENDIENTE
                    </span>
                  )}
                  {isSuspended && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      <AlertTriangle className="w-3 h-3" /> SUSPENDIDO
                    </span>
                  )}
                  {isCancelled && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                      <AlertCircle className="w-3 h-3" /> CANCELADO
                    </span>
                  )}
                </div>
              </div>

              {/* Match Teams & Score Display */}
              <div className="py-4 grid grid-cols-7 items-center text-center">
                {/* Home Team */}
                <div className="col-span-3 text-right pr-2">
                  <div className="font-bold text-sm sm:text-base text-slate-100 truncate">
                    {match.home_team?.name || 'Local'}
                  </div>
                  <div className="text-[11px] font-mono text-emerald-400">
                    {match.home_team?.short_name}
                  </div>
                </div>

                {/* Score or VS Badge */}
                <div className="col-span-1 flex items-center justify-center">
                  {isPlayed ? (
                    <div className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-slate-900 border border-slate-700 text-base sm:text-lg font-black font-mono text-white shadow-inner">
                      <span className={match.home_score! > match.away_score! ? 'text-emerald-400' : 'text-slate-200'}>
                        {match.home_score}
                      </span>
                      <span className="text-slate-500">-</span>
                      <span className={match.away_score! > match.home_score! ? 'text-emerald-400' : 'text-slate-200'}>
                        {match.away_score}
                      </span>
                    </div>
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-slate-800/80 border border-slate-700 flex items-center justify-center text-[10px] font-bold text-slate-400">
                      VS
                    </div>
                  )}
                </div>

                {/* Away Team */}
                <div className="col-span-3 text-left pl-2">
                  <div className="font-bold text-sm sm:text-base text-slate-100 truncate">
                    {match.away_team?.name || 'Visitante'}
                  </div>
                  <div className="text-[11px] font-mono text-emerald-400">
                    {match.away_team?.short_name}
                  </div>
                </div>
              </div>

              {/* Action Buttons (Admin Only) */}
              {isAdmin && (
                <div className="pt-3 border-t border-slate-800/60 flex flex-wrap items-center justify-end gap-2 text-xs">
                  {isPending && (
                    <>
                      <button
                        onClick={() => onOpenResultModal(match)}
                        className="px-2.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium transition-colors flex items-center gap-1"
                      >
                        <PlusCircle className="w-3.5 h-3.5" />
                        Cargar Resultado
                      </button>

                      <button
                        onClick={() => onUpdateStatus(match, 'SUSPENDIDO')}
                        className="px-2 py-1.5 rounded-lg bg-amber-950 hover:bg-amber-900 text-amber-300 border border-amber-800 font-medium transition-colors"
                      >
                        Suspender
                      </button>

                      <button
                        onClick={() => onUpdateStatus(match, 'CANCELADO')}
                        className="px-2 py-1.5 rounded-lg bg-rose-950 hover:bg-rose-900 text-rose-300 border border-rose-800 font-medium transition-colors"
                      >
                        Cancelar
                      </button>
                    </>
                  )}

                  {isPlayed && (
                    <button
                      onClick={() => onOpenStatsModal(match)}
                      className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium transition-colors flex items-center gap-1.5"
                    >
                      <BarChart3 className="w-3.5 h-3.5 text-yellow-400" />
                      Estadísticas (Goles / Tarjetas)
                    </button>
                  )}

                  {(isSuspended || isCancelled) && (
                    <button
                      onClick={() => onRescheduleMatch(match)}
                      className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition-colors flex items-center gap-1.5 shadow-md shadow-indigo-900/30"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      Reprogramar Automáticamente
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import { Shield, Phone, User, Users, ChevronDown, ChevronUp, CheckCircle2 } from 'lucide-react';

interface TeamsViewProps {
  teams: any[];
  loading?: boolean;
}

export const TeamsView: React.FC<TeamsViewProps> = ({ teams, loading }) => {
  const [expandedTeamId, setExpandedTeamId] = useState<string | null>(null);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-emerald-400 font-medium">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mr-3"></div>
        Cargando equipos...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl sm:text-2xl font-heading font-bold text-white flex items-center gap-2">
          <Shield className="w-6 h-6 text-emerald-400" />
          Equipos y Planteles Habilitados
        </h2>
        <p className="text-xs sm:text-sm text-slate-400">
          Clubes participantes y nómina de jugadores habilitados para disputar el torneo.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {teams.map((t) => {
          const isExpanded = expandedTeamId === t.id;
          return (
            <div key={t.id} className="glass-card rounded-2xl p-5 border border-slate-800 transition-all">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center font-extrabold text-emerald-400 text-lg shadow-md">
                    {t.short_name}
                  </div>
                  <div>
                    <h3 className="text-base sm:text-lg font-bold text-white leading-tight">
                      {t.name}
                    </h3>
                    <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
                      <span className="flex items-center gap-1">
                        <User className="w-3.5 h-3.5 text-slate-500" />
                        {t.delegate_name}
                      </span>
                      {t.delegate_phone && (
                        <span className="flex items-center gap-1 text-slate-500 font-mono">
                          <Phone className="w-3.5 h-3.5" />
                          {t.delegate_phone}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => setExpandedTeamId(isExpanded ? null : t.id)}
                  className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white border border-slate-700 transition-colors"
                >
                  {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>
              </div>

              {/* Player Count & Quick Summary */}
              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                <span className="flex items-center gap-1 font-medium text-slate-300">
                  <Users className="w-3.5 h-3.5 text-emerald-400" />
                  {t.players?.length || 0} Jugadores Habilitados
                </span>
                <button
                  onClick={() => setExpandedTeamId(isExpanded ? null : t.id)}
                  className="text-emerald-400 hover:underline font-semibold"
                >
                  {isExpanded ? 'Ocultar plantel' : 'Ver plantel'}
                </button>
              </div>

              {/* Collapsible Player Roster */}
              {isExpanded && (
                <div className="mt-3 pt-3 border-t border-slate-800/60">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                    {t.players && t.players.length > 0 ? (
                      t.players.map((p: any) => (
                        <div
                          key={p.id}
                          className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800"
                        >
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800/50 flex items-center justify-center font-mono font-bold text-[10px]">
                              {p.jersey_number}
                            </span>
                            <span className="font-medium text-slate-200 truncate">
                              {p.first_name} {p.last_name}
                            </span>
                          </div>
                          <span title="Habilitado">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          </span>
                        </div>
                      ))
                    ) : (
                      <div className="col-span-2 text-slate-500 text-center py-2">
                        No hay jugadores registrados aún
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

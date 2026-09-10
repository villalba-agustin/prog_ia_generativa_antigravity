import React, { useState, useEffect, useCallback } from 'react';
import { api } from './api';
import {
  Tournament, Standing, RoundWithMatches, Match, TopScorer,
  FairPlay, User
} from './types';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyTeam = any;

import { Navbar } from './components/Navbar';
import { StandingsTable } from './components/StandingsTable';
import { FixtureView } from './components/FixtureView';
import { ScorersView } from './components/ScorersView';
import { FairPlayView } from './components/FairPlayView';
import { TeamsView } from './components/TeamsView';
import { LoginModal } from './components/LoginModal';
import { MatchResultModal } from './components/MatchResultModal';
import { StatsModal } from './components/StatsModal';
import { AdminPanel } from './components/AdminPanel';

// ─── Types ────────────────────────────────────────────────────────────────────

type Tab = 'standings' | 'fixture' | 'results' | 'scorers' | 'fairplay' | 'teams' | 'admin' | 'delegate';

interface AppState {
  tournament: Tournament | null;
  standings: Standing[];
  fixture: RoundWithMatches[];
  results: Match[];
  scorers: TopScorer[];
  fairplay: FairPlay[];
  teams: AnyTeam[];
}

// ─── Loader Skeleton ──────────────────────────────────────────────────────────

const FullPageLoader: React.FC = () => (
  <div className="min-h-screen bg-slate-950 flex items-center justify-center">
    <div className="text-center">
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-emerald-600 to-green-400 flex items-center justify-center shadow-2xl shadow-emerald-500/30 mx-auto mb-4 animate-pulse">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" className="w-9 h-9">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
        </svg>
      </div>
      <p className="text-emerald-400 font-semibold animate-pulse">Cargando Liga de Barrios y Fincas...</p>
    </div>
  </div>
);

// ─── Hero / Welcome Banner ────────────────────────────────────────────────────

const HeroBanner: React.FC<{ tournament: Tournament | null }> = ({ tournament }) => (
  <div className="relative overflow-hidden rounded-2xl mb-6 bg-gradient-to-br from-emerald-950 via-slate-900 to-slate-950 border border-emerald-800/40 shadow-2xl shadow-emerald-900/20">
    {/* Decorative background elements */}
    <div className="absolute inset-0 opacity-10">
      <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
      <div className="absolute bottom-0 left-0 w-48 h-48 bg-green-600 rounded-full blur-3xl translate-y-1/3 -translate-x-1/4" />
    </div>
    <div className="relative px-6 py-8 sm:py-10">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-emerald-600 to-green-400 flex items-center justify-center shadow-lg shadow-emerald-500/30 shrink-0">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" className="w-7 h-7">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
          </svg>
        </div>
        <div>
          <h1 className="font-heading text-2xl sm:text-3xl font-extrabold text-white leading-none tracking-tight">
            Liga de Barrios <span className="text-emerald-400">&amp; Fincas</span>
          </h1>
          <p className="text-emerald-400/70 text-sm font-medium uppercase tracking-widest">
            Torneo Amateur Oficial 2026
          </p>
        </div>
      </div>
      <p className="text-slate-400 text-sm sm:text-base max-w-xl mt-2">
        Seguí en vivo las posiciones, el fixture, los resultados y las estadísticas de todos los partidos.
        {tournament && (
          <span className="ml-2 text-emerald-400 font-medium">{tournament.name}</span>
        )}
      </p>
    </div>
  </div>
);

// ─── Results View (inlined for simplicity) ────────────────────────────────────

const ResultsView: React.FC<{ results: Match[]; loading?: boolean }> = ({ results, loading }) => {
  if (loading) return (
    <div className="flex items-center justify-center p-12 text-emerald-400 font-medium">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mr-3" />
      Cargando resultados...
    </div>
  );
  if (!results || results.length === 0) return (
    <div className="p-12 text-center text-slate-400 glass-card rounded-2xl">
      <p className="text-lg font-bold text-slate-300">No hay resultados aún</p>
      <p className="text-sm text-slate-500 mt-1">Los resultados aparecerán aquí una vez que se jueguen los partidos.</p>
    </div>
  );
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-heading font-bold text-white flex items-center gap-2">
        <span className="w-5 h-5 text-yellow-400">🏆</span>
        Últimos Resultados
      </h2>
      <div className="grid gap-3">
        {results.map(match => (
          <div key={match.id} className="glass-card rounded-xl p-4 border border-slate-800 hover:border-emerald-800/50 transition-colors">
            <div className="flex items-center justify-between gap-4">
              <span className="text-sm text-slate-300 font-semibold text-right flex-1 truncate">
                {match.home_team?.name ?? 'Local'}
              </span>
              <div className="flex items-center gap-2 shrink-0">
                <span className="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center text-white font-extrabold text-base">
                  {match.home_score ?? '-'}
                </span>
                <span className="text-slate-500 text-xs font-bold">vs</span>
                <span className="w-8 h-8 bg-slate-700 rounded-lg flex items-center justify-center text-white font-extrabold text-base">
                  {match.away_score ?? '-'}
                </span>
              </div>
              <span className="text-sm text-slate-300 font-semibold flex-1 truncate">
                {match.away_team?.name ?? 'Visitante'}
              </span>
            </div>
            <div className="mt-2 flex items-center justify-center gap-3 text-xs text-slate-500">
              <span>📅 {match.match_date}</span>
              <span>⏰ {match.start_time?.slice(0, 5)}</span>
              {match.pitch && <span>📍 {match.pitch.name}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── Main App ─────────────────────────────────────────────────────────────────

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('standings');
  const [appData, setAppData] = useState<AppState>({
    tournament: null,
    standings: [],
    fixture: [],
    results: [],
    scorers: [],
    fairplay: [],
    teams: [],
  });
  const [loading, setLoading] = useState(true);
  const [dataError, setDataError] = useState<string | null>(null);

  // Auth state
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [showLoginModal, setShowLoginModal] = useState(false);

  // Modal state
  const [resultModalMatch, setResultModalMatch] = useState<Match | null>(null);
  const [statsModalMatch, setStatsModalMatch] = useState<Match | null>(null);

  // ── Fetch all public data ──────────────────────────────────────────────────

  const fetchData = useCallback(async () => {
    try {
      setDataError(null);
      const [summaryRes, fixtureRes, resultsRes, fairplayRes, teamsRes] = await Promise.allSettled([
        api.getPublicSummary(),
        api.getPublicFixture(),
        api.getPublicResults(),
        api.getPublicCards(),
        api.getPublicTeams(),
      ]);

      const summary = summaryRes.status === 'fulfilled' ? summaryRes.value : null;
      const fixture = fixtureRes.status === 'fulfilled' ? fixtureRes.value : [];
      const results = resultsRes.status === 'fulfilled' ? resultsRes.value : [];
      const fairplay = fairplayRes.status === 'fulfilled' ? fairplayRes.value : [];
      const teams = teamsRes.status === 'fulfilled' ? teamsRes.value : [];

      setAppData({
        tournament: summary?.tournament ?? null,
        standings: summary?.standings ?? [],
        fixture,
        results,
        scorers: summary?.top_scorers ?? [],
        fairplay,
        teams,
      });
    } catch (err: any) {
      setDataError('No se pudo conectar con el servidor. Verificá que el backend esté corriendo en http://localhost:8000');
    } finally {
      setLoading(false);
    }
  }, []);

  // ── Auth: restore session on mount ────────────────────────────────────────

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      api.getMe()
        .then(user => setCurrentUser(user))
        .catch(() => {
          localStorage.removeItem('token');
          setCurrentUser(null);
        });
    }
    fetchData();
  }, [fetchData]);

  // ── Auth handlers ─────────────────────────────────────────────────────────

  const handleLoginSuccess = (user: User) => {
    setCurrentUser(user);
    setShowLoginModal(false);
    if (user.role === 'ADMINISTRADOR') setActiveTab('admin');
  };

  const handleLogout = () => {
    api.logout();
    setCurrentUser(null);
    setActiveTab('standings');
  };

  // ── Match action handlers ─────────────────────────────────────────────────

  const handleReschedule = async (match: Match) => {
    if (!confirm(`¿Reprogramar automáticamente el partido ${match.home_team?.name} vs ${match.away_team?.name}?`)) return;
    try {
      await api.rescheduleMatch(match.id);
      await fetchData();
    } catch (err: any) {
      alert(`Error al reprogramar: ${err.message}`);
    }
  };

  const handleUpdateStatus = async (match: Match, status: 'SUSPENDIDO' | 'CANCELADO') => {
    const label = status === 'SUSPENDIDO' ? 'suspender' : 'cancelar';
    if (!confirm(`¿Confirmar ${label} el partido ${match.home_team?.name} vs ${match.away_team?.name}?`)) return;
    try {
      await api.updateMatchStatus(match.id, status);
      await fetchData();
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────

  if (loading) return <FullPageLoader />;

  const renderContent = () => {
    if (dataError) {
      return (
        <div className="glass-card rounded-2xl p-8 text-center border border-rose-800/40">
          <p className="text-rose-400 font-bold text-lg mb-2">⚠ Error de conexión</p>
          <p className="text-slate-400 text-sm">{dataError}</p>
          <button
            onClick={fetchData}
            className="mt-4 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Reintentar
          </button>
        </div>
      );
    }

    switch (activeTab) {
      case 'standings':
        return <StandingsTable standings={appData.standings} />;

      case 'fixture':
        return (
          <FixtureView
            fixture={appData.fixture}
            currentUser={currentUser}
            onOpenResultModal={setResultModalMatch}
            onOpenStatsModal={setStatsModalMatch}
            onRescheduleMatch={handleReschedule}
            onUpdateStatus={handleUpdateStatus}
          />
        );

      case 'results':
        return <ResultsView results={appData.results} />;

      case 'scorers':
        return <ScorersView scorers={appData.scorers} />;

      case 'fairplay':
        return <FairPlayView fairPlayList={appData.fairplay} />;

      case 'teams':
        return <TeamsView teams={appData.teams} />;

      case 'admin':
        if (currentUser?.role !== 'ADMINISTRADOR') {
          setActiveTab('standings');
          return null;
        }
        return (
          <AdminPanel
            tournament={appData.tournament}
            onRefreshData={fetchData}
          />
        );

      case 'delegate':
        if (!currentUser) {
          setActiveTab('standings');
          return null;
        }
        return (
          <div className="glass-card rounded-2xl p-8 border border-blue-800/30 text-center">
            <p className="text-blue-300 font-bold text-lg mb-2">Panel del Delegado</p>
            <p className="text-slate-400 text-sm">
              Sesión activa como <span className="text-white font-semibold">{currentUser.email}</span>.
              Consultá los datos de tu equipo en la sección Equipos.
            </p>
            <button
              onClick={() => setActiveTab('teams')}
              className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors"
            >
              Ver Equipos
            </button>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={(tab) => setActiveTab(tab as Tab)}
        currentUser={currentUser}
        onOpenLogin={() => setShowLoginModal(true)}
        onLogout={handleLogout}
      />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {/* Show hero only on standings tab */}
        {activeTab === 'standings' && <HeroBanner tournament={appData.tournament} />}

        {/* Page Content */}
        <div className="animate-fade-in">
          {renderContent()}
        </div>
      </main>

      {/* Refresh button (floating) */}
      <button
        onClick={fetchData}
        title="Actualizar datos"
        className="fixed bottom-6 right-6 w-11 h-11 rounded-full bg-emerald-700 hover:bg-emerald-600 shadow-lg shadow-emerald-900/50 flex items-center justify-center transition-all hover:scale-110 z-30"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="1 4 1 10 7 10" /><polyline points="23 20 23 14 17 14" />
          <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
        </svg>
      </button>

      {/* Login Modal */}
      <LoginModal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
        onLoginSuccess={handleLoginSuccess}
      />

      {/* Match Result Modal */}
      {resultModalMatch && (
        <MatchResultModal
          match={resultModalMatch}
          onClose={() => setResultModalMatch(null)}
          onSuccess={() => {
            setResultModalMatch(null);
            fetchData();
          }}
        />
      )}

      {/* Stats Modal */}
      {statsModalMatch && (
        <StatsModal
          match={statsModalMatch}
          onClose={() => setStatsModalMatch(null)}
          onSuccess={() => {
            setStatsModalMatch(null);
            fetchData();
          }}
        />
      )}

      {/* Footer */}
      <footer className="mt-12 border-t border-slate-800/60 py-6 text-center">
        <p className="text-slate-500 text-xs">
          Liga de Barrios &amp; Fincas &copy; 2026 · Sistema de Gestión de Torneos Amateurs
        </p>
      </footer>
    </div>
  );
}

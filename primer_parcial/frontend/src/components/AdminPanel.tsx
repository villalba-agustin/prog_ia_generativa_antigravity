import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Tournament, Team, Player } from '../types';
import { Settings, Calendar, Plus, Users, Shield, Check, AlertCircle, UserCheck, UserX } from 'lucide-react';

interface AdminPanelProps {
  tournament: Tournament | null;
  onRefreshData: () => void;
}

export const AdminPanel: React.FC<AdminPanelProps> = ({ tournament, onRefreshData }) => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeamId, setSelectedTeamId] = useState<string>('');
  const [players, setPlayers] = useState<Player[]>([]);
  
  // Team Form
  const [teamName, setTeamName] = useState('');
  const [teamShortName, setTeamShortName] = useState('');
  const [teamDelegate, setTeamDelegate] = useState('');
  const [teamPhone, setTeamPhone] = useState('');

  // Player Form
  const [playerFirstName, setPlayerFirstName] = useState('');
  const [playerLastName, setPlayerLastName] = useState('');
  const [playerDni, setPlayerDni] = useState('');
  const [playerBirthDate, setPlayerBirthDate] = useState('2000-01-01');
  const [playerJersey, setPlayerJersey] = useState(1);

  const [loadingAction, setLoadingAction] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const loadTeams = async () => {
    try {
      const data = await api.getTeams();
      setTeams(data);
      if (data.length > 0 && !selectedTeamId) {
        setSelectedTeamId(data[0].id);
      }
    } catch (err: any) {
      console.error(err);
    }
  };

  const loadPlayers = async (tId: string) => {
    if (!tId) return;
    try {
      const data = await api.getTeamPlayers(tId);
      setPlayers(data);
    } catch (err: any) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadTeams();
  }, []);

  useEffect(() => {
    if (selectedTeamId) {
      loadPlayers(selectedTeamId);
    }
  }, [selectedTeamId]);

  const handleGenerateFixture = async () => {
    if (!tournament) return;
    if (!confirm('¿Desea generar el fixture automático de todos contra todos a 1 rueda en 4 canchas? Una vez generado, quedará bloqueado para edición manual.')) return;

    setLoadingAction(true);
    setMessage(null);
    try {
      await api.generateFixture(tournament.id);
      setMessage({ type: 'success', text: '¡Fixture generado exitosamente!' });
      onRefreshData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Error al generar fixture' });
    } finally {
      setLoadingAction(false);
    }
  };

  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingAction(true);
    setMessage(null);
    try {
      await api.createTeam({
        name: teamName,
        short_name: teamShortName,
        delegate_name: teamDelegate,
        delegate_phone: teamPhone
      });
      setMessage({ type: 'success', text: `Equipo ${teamName} creado correctamente.` });
      setTeamName('');
      setTeamShortName('');
      setTeamDelegate('');
      setTeamPhone('');
      await loadTeams();
      onRefreshData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setLoadingAction(false);
    }
  };

  const handleCreatePlayer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTeamId) {
      setMessage({ type: 'error', text: 'Seleccione un equipo' });
      return;
    }
    setLoadingAction(true);
    setMessage(null);
    try {
      await api.createPlayer({
        team_id: selectedTeamId,
        first_name: playerFirstName,
        last_name: playerLastName,
        dni: playerDni,
        birth_date: playerBirthDate,
        jersey_number: playerJersey
      });
      setMessage({ type: 'success', text: `Jugador ${playerFirstName} ${playerLastName} registrado.` });
      setPlayerFirstName('');
      setPlayerLastName('');
      setPlayerDni('');
      setPlayerJersey(prev => prev + 1);
      await loadPlayers(selectedTeamId);
      onRefreshData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setLoadingAction(false);
    }
  };

  const handleTogglePlayer = async (playerId: string) => {
    try {
      await api.togglePlayerEnabled(playerId);
      await loadPlayers(selectedTeamId);
      onRefreshData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl sm:text-2xl font-heading font-bold text-white flex items-center gap-2">
          <Settings className="w-6 h-6 text-purple-400" />
          Panel de Administración General
        </h2>
        <p className="text-xs sm:text-sm text-slate-400">
          Gestión del torneo activo, generación de calendario oficial, equipos y habilitación de planteles.
        </p>
      </div>

      {message && (
        <div className={`p-4 rounded-xl text-xs flex items-center gap-2 border ${
          message.type === 'success'
            ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
            : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
        }`}>
          {message.type === 'success' ? <Check className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          {message.text}
        </div>
      )}

      {/* Section 1: Tournament & Fixture Status */}
      <div className="glass-card rounded-2xl p-5 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-200 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-emerald-400" />
              Estado del Fixture
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Torneo: <strong className="text-slate-300">{tournament?.name || 'No activo'}</strong>
            </p>
          </div>

          <div>
            {tournament?.fixture_generated ? (
              <span className="px-3 py-1.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                ✓ Fixture Oficial Generado y Bloqueado
              </span>
            ) : (
              <button
                onClick={handleGenerateFixture}
                disabled={loadingAction}
                className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-purple-600 hover:bg-purple-500 shadow-lg shadow-purple-900/30 transition-all disabled:opacity-50"
              >
                Generar Fixture Automático
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Section 2: Create Team & Add Player */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Create Team Form */}
        <div className="glass-card rounded-2xl p-5 border border-slate-800">
          <h3 className="text-base font-bold text-slate-200 flex items-center gap-2 mb-3">
            <Shield className="w-5 h-5 text-emerald-400" />
            Inscribir Nuevo Equipo
          </h3>
          <form onSubmit={handleCreateTeam} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Nombre del Equipo</label>
              <input
                type="text"
                required
                value={teamName}
                onChange={e => setTeamName(e.target.value)}
                placeholder="Ej: Deportivo Central"
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:border-emerald-500 focus:outline-none"
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Nombre Corto</label>
                <input
                  type="text"
                  required
                  maxLength={10}
                  value={teamShortName}
                  onChange={e => setTeamShortName(e.target.value.toUpperCase())}
                  placeholder="DC"
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:border-emerald-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Teléfono Delegado</label>
                <input
                  type="text"
                  required
                  value={teamPhone}
                  onChange={e => setTeamPhone(e.target.value)}
                  placeholder="381-1234567"
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:border-emerald-500 focus:outline-none"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Nombre del Delegado</label>
              <input
                type="text"
                required
                value={teamDelegate}
                onChange={e => setTeamDelegate(e.target.value)}
                placeholder="Juan Pérez"
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:border-emerald-500 focus:outline-none"
              />
            </div>

            <button
              type="submit"
              disabled={loadingAction || tournament?.fixture_generated}
              className="w-full py-2 rounded-xl text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-500 transition-all disabled:opacity-40"
            >
              {tournament?.fixture_generated ? 'Inscripciones Cerradas (Fixture ya generado)' : 'Registrar Equipo'}
            </button>
          </form>
        </div>

        {/* Add Player to Team Form */}
        <div className="glass-card rounded-2xl p-5 border border-slate-800">
          <h3 className="text-base font-bold text-slate-200 flex items-center gap-2 mb-3">
            <Users className="w-5 h-5 text-yellow-400" />
            Inscribir Jugador
          </h3>
          <form onSubmit={handleCreatePlayer} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Equipo de Destino</label>
              <select
                value={selectedTeamId}
                onChange={e => setSelectedTeamId(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:border-emerald-500 focus:outline-none"
              >
                {teams.map(t => (
                  <option key={t.id} value={t.id}>{t.name} ({t.short_name})</option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Nombre</label>
                <input
                  type="text"
                  required
                  value={playerFirstName}
                  onChange={e => setPlayerFirstName(e.target.value)}
                  placeholder="Carlos"
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:border-emerald-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Apellido</label>
                <input
                  type="text"
                  required
                  value={playerLastName}
                  onChange={e => setPlayerLastName(e.target.value)}
                  placeholder="Gómez"
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:border-emerald-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div className="col-span-1">
                <label className="block text-xs font-semibold text-slate-400 mb-1">DNI</label>
                <input
                  type="text"
                  required
                  value={playerDni}
                  onChange={e => setPlayerDni(e.target.value)}
                  placeholder="40123456"
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:border-emerald-500 focus:outline-none"
                />
              </div>
              <div className="col-span-1">
                <label className="block text-xs font-semibold text-slate-400 mb-1">N° Camiseta</label>
                <input
                  type="number"
                  min="1"
                  max="99"
                  required
                  value={playerJersey}
                  onChange={e => setPlayerJersey(parseInt(e.target.value) || 1)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:border-emerald-500 focus:outline-none"
                />
              </div>
              <div className="col-span-1">
                <label className="block text-xs font-semibold text-slate-400 mb-1">Nacimiento</label>
                <input
                  type="date"
                  required
                  value={playerBirthDate}
                  onChange={e => setPlayerBirthDate(e.target.value)}
                  className="w-full px-2 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white focus:border-emerald-500 focus:outline-none"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loadingAction}
              className="w-full py-2 rounded-xl text-xs font-bold text-white bg-yellow-600 hover:bg-yellow-500 transition-all disabled:opacity-50"
            >
              Registrar Jugador
            </button>
          </form>
        </div>
      </div>

      {/* Section 3: Manage Player Enablement Status */}
      <div className="glass-card rounded-2xl p-5 border border-slate-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <h3 className="text-base font-bold text-slate-200 flex items-center gap-2">
            <UserCheck className="w-5 h-5 text-emerald-400" />
            Habilitación de Jugadores ({teams.find(t => t.id === selectedTeamId)?.name})
          </h3>
          <select
            value={selectedTeamId}
            onChange={e => setSelectedTeamId(e.target.value)}
            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white"
          >
            {teams.map(t => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {players.map(p => (
            <div key={p.id} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 truncate">
                <span className="w-6 h-6 rounded bg-slate-800 text-slate-300 font-mono font-bold flex items-center justify-center shrink-0">
                  #{p.jersey_number}
                </span>
                <div className="truncate">
                  <span className="font-semibold text-slate-200 block truncate">{p.first_name} {p.last_name}</span>
                  <span className="text-[10px] text-slate-500 font-mono">DNI: {p.dni}</span>
                </div>
              </div>

              <button
                onClick={() => handleTogglePlayer(p.id)}
                className={`px-2 py-1 rounded-lg text-[10px] font-bold flex items-center gap-1 transition-colors ${
                  p.is_enabled
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-rose-950/40 hover:text-rose-300'
                    : 'bg-rose-500/20 text-rose-300 border border-rose-500/30 hover:bg-emerald-950/40 hover:text-emerald-300'
                }`}
              >
                {p.is_enabled ? <UserCheck className="w-3 h-3" /> : <UserX className="w-3 h-3" />}
                {p.is_enabled ? 'Habilitado' : 'Inhabilitado'}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

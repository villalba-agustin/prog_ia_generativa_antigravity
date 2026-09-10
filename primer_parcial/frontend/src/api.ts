import {
  Tournament, Team, Player, Match, RoundWithMatches,
  Standing, TopScorer, FairPlay, User, MatchStat
} from './types';

const API_BASE = '/api/v1';

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('token');
  return token ? { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = 'Error en la solicitud';
    try {
      const body = await res.json();
      errorDetail = body.detail || JSON.stringify(body);
    } catch {
      errorDetail = res.statusText || `${res.status}`;
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // Public
  async getPublicSummary(): Promise<{
    tournament: Tournament | null;
    standings: Standing[];
    recent_results: Match[];
    upcoming_matches: Match[];
    top_scorers: TopScorer[];
  }> {
    const res = await fetch(`${API_BASE}/public/summary`);
    return handleResponse(res);
  },

  async getPublicStandings(): Promise<Standing[]> {
    const res = await fetch(`${API_BASE}/public/standings`);
    return handleResponse(res);
  },

  async getPublicFixture(): Promise<RoundWithMatches[]> {
    const res = await fetch(`${API_BASE}/public/fixture`);
    return handleResponse(res);
  },

  async getPublicResults(): Promise<Match[]> {
    const res = await fetch(`${API_BASE}/public/results`);
    return handleResponse(res);
  },

  async getPublicScorers(): Promise<TopScorer[]> {
    const res = await fetch(`${API_BASE}/public/scorers`);
    return handleResponse(res);
  },

  async getPublicCards(): Promise<FairPlay[]> {
    const res = await fetch(`${API_BASE}/public/cards`);
    return handleResponse(res);
  },

  async getPublicTeams(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/public/teams`);
    return handleResponse(res);
  },

  // Auth
  async login(email: string, password: string): Promise<{ access_token: string; role: 'ADMINISTRADOR' | 'DELEGADO'; team_id?: string; email: string }> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await handleResponse<{ access_token: string; role: 'ADMINISTRADOR' | 'DELEGADO'; team_id?: string; email: string }>(res);
    localStorage.setItem('token', data.access_token);
    return data;
  },

  async getMe(): Promise<User> {
    const res = await fetch(`${API_BASE}/auth/me`, { headers: getAuthHeaders() });
    return handleResponse(res);
  },

  logout() {
    localStorage.removeItem('token');
  },

  // Admin / Matches
  async recordResult(matchId: string, home_score: number, away_score: number): Promise<Match> {
    const res = await fetch(`${API_BASE}/matches/${matchId}/result`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ home_score, away_score })
    });
    return handleResponse(res);
  },

  async rescheduleMatch(matchId: string, target_date?: string): Promise<Match> {
    const res = await fetch(`${API_BASE}/matches/${matchId}/reschedule`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(target_date ? { target_date } : {})
    });
    return handleResponse(res);
  },

  async updateMatchStatus(matchId: string, status: 'SUSPENDIDO' | 'CANCELADO'): Promise<Match> {
    const res = await fetch(`${API_BASE}/matches/${matchId}/status`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ status })
    });
    return handleResponse(res);
  },

  async getMatchStats(matchId: string): Promise<MatchStat[]> {
    const res = await fetch(`${API_BASE}/stats/matches/${matchId}`, { headers: getAuthHeaders() });
    return handleResponse(res);
  },

  async recordMatchStats(matchId: string, stats: { player_id: string; team_id: string; goals: number; yellow_cards: number; red_cards: number }[]): Promise<MatchStat[]> {
    const res = await fetch(`${API_BASE}/stats/matches/${matchId}`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ stats })
    });
    return handleResponse(res);
  },

  async generateFixture(tournamentId: string): Promise<any[]> {
    const res = await fetch(`${API_BASE}/tournaments/${tournamentId}/generate-fixture`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    return handleResponse(res);
  },

  // Teams & Players
  async getTeams(): Promise<Team[]> {
    const res = await fetch(`${API_BASE}/teams/`);
    return handleResponse(res);
  },

  async getTeamPlayers(teamId: string): Promise<Player[]> {
    const res = await fetch(`${API_BASE}/teams/${teamId}/players`);
    return handleResponse(res);
  },

  async updateTeam(teamId: string, data: Partial<Team>): Promise<Team> {
    const res = await fetch(`${API_BASE}/teams/${teamId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    });
    return handleResponse(res);
  },

  async createTeam(data: { name: string; short_name: string; delegate_name: string; delegate_phone: string }): Promise<Team> {
    const res = await fetch(`${API_BASE}/teams/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    });
    return handleResponse(res);
  },

  async createPlayer(data: { team_id: string; first_name: string; last_name: string; dni: string; birth_date: string; jersey_number: number }): Promise<Player> {
    const res = await fetch(`${API_BASE}/players/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    });
    return handleResponse(res);
  },

  async togglePlayerEnabled(playerId: string): Promise<Player> {
    const res = await fetch(`${API_BASE}/players/${playerId}/toggle-enable`, {
      method: 'PATCH',
      headers: getAuthHeaders()
    });
    return handleResponse(res);
  }
};

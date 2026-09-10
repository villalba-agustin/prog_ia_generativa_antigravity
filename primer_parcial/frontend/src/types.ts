export interface Tournament {
  id: string;
  name: string;
  start_date: string;
  is_active: boolean;
  fixture_generated: boolean;
}

export interface Team {
  id: string;
  tournament_id: string;
  name: string;
  short_name: string;
  logo_url: string | null;
  delegate_name: string;
  delegate_phone: string;
  is_active: boolean;
  players_count?: number;
}

export interface Player {
  id: string;
  team_id: string;
  first_name: string;
  last_name: string;
  dni: string;
  birth_date: string;
  jersey_number: number;
  is_enabled: boolean;
}

export interface Pitch {
  id: number;
  name: string;
  pitch_number: number;
  is_available: boolean;
}

export interface Match {
  id: string;
  round_id: string;
  tournament_id: string;
  home_team_id: string;
  away_team_id: string;
  pitch_id: number;
  match_date: string;
  start_time: string;
  end_time: string;
  home_score: number | null;
  away_score: number | null;
  status: 'PENDIENTE' | 'JUGADO' | 'SUSPENDIDO' | 'CANCELADO';
  is_locked: boolean;
  played_at: string | null;
  home_team?: { id: string; name: string; short_name: string; logo_url: string | null };
  away_team?: { id: string; name: string; short_name: string; logo_url: string | null };
  pitch?: Pitch;
}

export interface Round {
  id: string;
  tournament_id: string;
  round_number: number;
  name: string;
  scheduled_date: string;
  status: string;
}

export interface RoundWithMatches {
  round: Round;
  matches: Match[];
}

export interface Standing {
  id: string;
  tournament_id: string;
  team_id: string;
  team_name: string;
  team_short_name: string;
  team_logo_url: string | null;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_diff: number;
  points: number;
  fair_play_score: number;
  position: number;
}

export interface TopScorer {
  player_id: string;
  player_name: string;
  team_name: string;
  jersey_number: number;
  goals: number;
}

export interface FairPlay {
  team_id: string;
  team_name: string;
  yellow_cards: number;
  red_cards: number;
  fair_play_score: number;
}

export interface User {
  id: string;
  email: string;
  role: 'ADMINISTRADOR' | 'DELEGADO';
  team_id: string | null;
  is_active: boolean;
}

export interface MatchStat {
  id: string;
  match_id: string;
  team_id: string;
  player_id: string;
  goals: number;
  yellow_cards: number;
  red_cards: number;
}

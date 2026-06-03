export type Game = {
  game_id: string;
  name: string;
  short_name: string;
  date: string;

  home_team: string;
  home_team_abbr: string;
  home_score: number;
  home_record: string;

  away_team: string;
  away_team_abbr: string;
  away_score: number;
  away_record: string;

  period: number;
  clock: string;
  status: string;
  detail: string;

  venue: string;
  series: string;
  broadcast: string;

  spread: string;
  over_under: number | null;

  home_win_probability: number;
};

export type TimelinePoint = {
  time: string;
  home_win_probability: number;
};

export type LivePlay = {
  id?: string;
  sequence_number?: string | number;
  period?: number | null;
  clock?: string | null;
  text?: string | null;
  short_text?: string | null;
  type?: string | null;
  team?: string | null;
  home_score?: number | string | null;
  away_score?: number | string | null;
  scoring_play?: boolean | null;
  score_value?: number | null;
  shooting_play?: boolean | null;
  points_attempted?: number | null;
  wallclock?: string | null;
  home_win_probability?: number | null;
};

export type GameStateDashboard = {
  game_id: string;
  home_team: string;
  away_team: string;
  home_team_abbr: string;
  away_team_abbr: string;
  home_score: number;
  away_score: number;
  score_diff: number;
  period: number | null;
  clock: string | null;
  possession_team: string | null;
  home_win_probability: number;
  home_fouls: number | null;
  away_fouls: number | null;
  home_in_bonus: boolean;
  away_in_bonus: boolean;
};
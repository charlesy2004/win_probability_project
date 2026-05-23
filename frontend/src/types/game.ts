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
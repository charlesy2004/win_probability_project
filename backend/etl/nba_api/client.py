from nba_api.stats.endpoints import leaguegamelog


def fetch_league_game_log(season: str, season_type: str):
    response = leaguegamelog.LeagueGameLog(
        season=season,
        season_type_all_star=season_type,
        player_or_team_abbreviation="T",
        timeout=60,
    )

    return response.get_data_frames()[0]
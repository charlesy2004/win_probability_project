from nba_api.stats.endpoints import leaguegamelog

SEASON_TYPE = "Regular Season"


def fetch_league_game_log(season: str):
    response = leaguegamelog.LeagueGameLog(
        season=season,
        season_type_all_star=SEASON_TYPE,
        player_or_team_abbreviation="T",
        timeout=60,
    )

    return response.get_data_frames()[0]
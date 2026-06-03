from etl.nba_api.client import fetch_league_game_log
from etl.nba_api.loaders import load_games, load_teams
from etl.nba_api.transforms import build_games_table, build_teams_table


def load_historical_games_for_season(season: str) -> None:
    print(f"Fetching NBA game log for {season}")

    game_log_df = fetch_league_game_log(season)

    print("Transforming teams")
    teams_df = build_teams_table(game_log_df)

    print("Transforming games")
    games_df = build_games_table(game_log_df, season)

    print(f"Loading {len(teams_df)} teams into database")
    teams_loaded = load_teams(teams_df)

    print(f"Loading {len(games_df)} games into database")
    games_loaded = load_games(games_df)

    print(
        f"Finished loading {season}: "
        f"teams_loaded={teams_loaded}, games_loaded={games_loaded}"
    )
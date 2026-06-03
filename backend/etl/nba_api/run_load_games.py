import argparse

from etl.nba_api.jobs import load_historical_games_for_season


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", required=True, help="Example: 2024-25")
    args = parser.parse_args()

    load_historical_games_for_season(args.season)


if __name__ == "__main__":
    main()
import argparse

from etl.nba_api.jobs import load_historical_games_for_season


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", required=True, help="Example: 2024-25")
    parser.add_argument(
        "--season-type",
        default="Regular Season",
        choices=["Regular Season", "Playoffs", "Pre Season", "All Star"],
        help='Example: "Regular Season" or "Playoffs"',
    )

    args = parser.parse_args()

    load_historical_games_for_season(
        season=args.season,
        season_type=args.season_type,
    )


if __name__ == "__main__":
    main()
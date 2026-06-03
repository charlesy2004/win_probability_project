import pandas as pd


def build_teams_table(game_log_df: pd.DataFrame) -> pd.DataFrame:
    teams_df = (
        game_log_df[
            [
                "TEAM_ID",
                "TEAM_ABBREVIATION",
                "TEAM_NAME",
            ]
        ]
        .drop_duplicates()
        .rename(
            columns={
                "TEAM_ID": "nba_team_id",
                "TEAM_ABBREVIATION": "abbreviation",
                "TEAM_NAME": "display_name",
            }
        )
    )

    teams_df["nba_team_id"] = teams_df["nba_team_id"].astype(str)
    teams_df["league"] = "nba"

    return teams_df[
        [
            "nba_team_id",
            "abbreviation",
            "display_name",
            "league",
        ]
    ]


def build_games_table(
    game_log_df: pd.DataFrame,
    season: str,
    season_type: str,
) -> pd.DataFrame:
    rows = []

    for game_id, game_df in game_log_df.groupby("GAME_ID"):
        if len(game_df) != 2:
            continue

        home_row = game_df[game_df["MATCHUP"].str.contains(" vs. ", regex=False)]
        away_row = game_df[game_df["MATCHUP"].str.contains(" @ ", regex=False)]

        if home_row.empty or away_row.empty:
            continue

        home = home_row.iloc[0]
        away = away_row.iloc[0]

        rows.append(
            {
                "nba_game_id": str(game_id),
                "season": season,
                "season_type": season_type,
                "game_date": pd.to_datetime(home["GAME_DATE"]),
                "home_team_id": str(home["TEAM_ID"]),
                "away_team_id": str(away["TEAM_ID"]),
                "home_team_name": home["TEAM_NAME"],
                "away_team_name": away["TEAM_NAME"],
                "home_team_abbr": home["TEAM_ABBREVIATION"],
                "away_team_abbr": away["TEAM_ABBREVIATION"],
                "home_score": int(home["PTS"]),
                "away_score": int(away["PTS"]),
                "home_win": bool(home["WL"] == "W"),
                "status": "final",
            }
        )

    games_df = pd.DataFrame(rows)

    if games_df.empty:
        return games_df

    return games_df.sort_values("game_date")
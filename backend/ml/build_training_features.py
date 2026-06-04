from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from db.session import engine
from ml.features import MODEL_FEATURE_COLUMNS, TARGET_COLUMN


OUTPUT_DIR = Path("ml/data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_training_features(seasons: list[str] | None = None) -> pd.DataFrame:
    query = """
        SELECT
            h.game_id,
            h.period,
            h.seconds_remaining,
            h.game_progress,
            h.home_score,
            h.away_score,
            h.score_diff,
            h.home_team_won,

            s.season,
            s.season_type,
            s.pregame_home_elo,
            s.pregame_away_elo,
            s.team_rating_diff,
            s.home_days_rest,
            s.away_days_rest,
            s.rest_diff,
            s.home_back_to_back,
            s.away_back_to_back

        FROM historical_game_states h
        JOIN game_team_strengths s
            ON h.game_id = s.nba_game_id
        WHERE h.home_team_won IS NOT NULL
    """

    params = {}

    if seasons:
        query += " AND s.season = ANY(%(seasons)s)"
        params["seasons"] = seasons

    query += """
        ORDER BY
            s.season,
            s.season_type,
            h.game_id,
            h.period,
            h.seconds_remaining DESC
    """

    df = pd.read_sql(query, engine, params=params)

    return df


def clean_training_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    bool_columns = [
        "home_back_to_back",
        "away_back_to_back",
        TARGET_COLUMN,
    ]

    for column in bool_columns:
        if column in df.columns:
            df[column] = df[column].astype(int)

    rest_columns = [
        "home_days_rest",
        "away_days_rest",
        "rest_diff",
    ]

    for column in rest_columns:
        if column in df.columns:
            df[column] = df[column].fillna(0)

    df = df.dropna(subset=MODEL_FEATURE_COLUMNS + [TARGET_COLUMN])

    return df


def save_training_features(df: pd.DataFrame, output_path: Path) -> None:
    df.to_parquet(output_path, index=False)
    print(f"Saved training features to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--seasons",
        nargs="+",
        help="Example: 2022-23 2023-24 2024-25 2025-26",
    )
    parser.add_argument(
        "--output",
        default="ml/data/training_features.parquet",
    )
    args = parser.parse_args()

    print("Loading training features")
    df = load_training_features(seasons=args.seasons)

    print(f"Loaded rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")

    if df.empty:
        raise ValueError("No training rows loaded. Check historical_game_states and game_team_strengths join.")

    print("Cleaning training features")
    df = clean_training_features(df)

    print(f"Rows after cleaning: {len(df)}")

    missing_counts = df[MODEL_FEATURE_COLUMNS + [TARGET_COLUMN]].isna().sum()
    print("Missing values:")
    print(missing_counts)

    save_training_features(df, Path(args.output))


if __name__ == "__main__":
    main()
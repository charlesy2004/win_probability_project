import time
from typing import Optional

import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder, playbyplayv2

from db.session import session_local
from services.historical_data_service import create_historical_game_state


SEASON = "2023-24"
SEASON_TYPE = "Regular Season"
MAX_GAMES = 10
REQUEST_SLEEP_SECONDS = 1.0


def parse_score(score_text: Optional[str]) -> tuple[Optional[int], Optional[int]]:
    """
    NBA play-by-play SCORE usually looks like:
    '24 - 21'
    Sometimes it is blank/None for non-scoring events.
    """
    if not score_text or not isinstance(score_text, str):
        return None, None

    parts = score_text.split(" - ")

    if len(parts) != 2:
        return None, None

    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None, None


def get_completed_game_ids(season: str, max_games: int) -> list[str]:
    finder = leaguegamefinder.LeagueGameFinder(
        season_nullable=season,
        season_type_nullable=SEASON_TYPE,
    )

    games_df = finder.get_data_frames()[0]

    # LeagueGameFinder returns one row per team per game, so GAME_ID repeats.
    game_ids = games_df["GAME_ID"].drop_duplicates().head(max_games).tolist()

    return game_ids


def get_final_score_from_pbp(pbp_df: pd.DataFrame) -> tuple[int, int]:
    scoring_rows = pbp_df[pbp_df["SCORE"].notna()].copy()

    if scoring_rows.empty:
        raise ValueError("No scoring rows found.")

    final_score_text = scoring_rows.iloc[-1]["SCORE"]
    score_a, score_b = parse_score(final_score_text)

    if score_a is None or score_b is None:
        raise ValueError(f"Could not parse final score: {final_score_text}")

    return score_a, score_b


def infer_home_away_names(pbp_df: pd.DataFrame) -> tuple[str, str]:
    """
    Simple starter version.

    NBA play-by-play has HOMEDESCRIPTION and VISITORDESCRIPTION columns,
    but not always clean team names. For now, use placeholders.
    Later we can join a boxscore endpoint to get exact home/away teams.
    """
    return "Home Team", "Away Team"


def backfill_game(db, game_id: str) -> int:
    pbp = playbyplayv2.PlayByPlayV2(game_id=game_id)
    pbp_df = pbp.get_data_frames()[0]

    if pbp_df.empty:
        print(f"No play-by-play found for {game_id}")
        return 0

    final_home_score, final_away_score = get_final_score_from_pbp(pbp_df)
    home_team, away_team = infer_home_away_names(pbp_df)

    inserted = 0

    current_home_score = 0
    current_away_score = 0

    # Use scoring events only for first version.
    scoring_rows = pbp_df[pbp_df["SCORE"].notna()].copy()

    for _, row in scoring_rows.iterrows():
        period = int(row["PERIOD"])
        clock = row["PCTIMESTRING"]

        parsed_home_score, parsed_away_score = parse_score(row["SCORE"])

        if parsed_home_score is None or parsed_away_score is None:
            continue

        current_home_score = parsed_home_score
        current_away_score = parsed_away_score

        create_historical_game_state(
            db=db,
            game_id=game_id,
            home_team=home_team,
            away_team=away_team,
            home_score=current_home_score,
            away_score=current_away_score,
            period=period,
            clock=clock,
            final_home_score=final_home_score,
            final_away_score=final_away_score,
        )

        inserted += 1

    return inserted


def main():
    db = session_local()

    try:
        game_ids = get_completed_game_ids(SEASON, MAX_GAMES)

        print(f"Found {len(game_ids)} games.")
        total_inserted = 0

        for game_id in game_ids:
            print(f"Backfilling game {game_id}...")

            try:
                inserted = backfill_game(db, game_id)
                total_inserted += inserted
                print(f"Inserted {inserted} rows for {game_id}.")
            except Exception as e:
                print(f"Failed on {game_id}: {e}")

            time.sleep(REQUEST_SLEEP_SECONDS)

        print(f"Done. Inserted {total_inserted} historical game-state rows.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
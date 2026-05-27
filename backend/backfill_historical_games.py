"""
Run this locally, not in Codespaces.

Codespaces/NBA.com may return 403 for nba_api.
This script uses nba_api locally to fetch historical NBA play-by-play,
convert it into game-state training rows, and upload those rows to Supabase.

It inserts rows into the historical_game_states table.
"""

import re
import time

import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder, playbyplayv3

from db.session import session_local
from services.historical_data_service import create_historical_game_state


SEASON = "2023-24"
SEASON_TYPE = "Regular Season"
MAX_GAMES = 1230
REQUEST_SLEEP_SECONDS = 1.0


def safe_int(value):
    """
    Safely convert score values to int.

    PlayByPlayV3 sometimes gives:
    - empty string ""
    - None
    - NaN

    Those should be skipped.
    """
    if value is None:
        return None

    if pd.isna(value):
        return None

    if value == "":
        return None

    try:
        return int(value)
    except ValueError:
        return None


def nba_clock_to_mmss(clock: str) -> str:
    """
    Convert NBA API V3 clock format like:
        PT11M38.00S

    into:
        11:38
    """
    if not isinstance(clock, str):
        return "0:00"

    match = re.match(r"PT(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?", clock)

    if not match:
        return "0:00"

    minutes = int(match.group(1) or 0)
    seconds = int(float(match.group(2) or 0))

    return f"{minutes}:{seconds:02d}"


def get_completed_game_ids(season: str, max_games: int) -> list[str]:
    """
    Gets completed game IDs for a season.

    LeagueGameFinder returns one row per team per game,
    so GAME_ID appears twice. We drop duplicates.
    """
    finder = leaguegamefinder.LeagueGameFinder(
        season_nullable=season,
        season_type_nullable=SEASON_TYPE,
    )

    games_df = finder.get_data_frames()[0]

    game_ids = games_df["GAME_ID"].drop_duplicates().head(max_games).tolist()

    return game_ids


def get_valid_score_rows(pbp_df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only rows where both home and away scores are valid numbers.
    """
    score_rows = pbp_df.copy()

    score_rows["scoreHomeParsed"] = score_rows["scoreHome"].apply(safe_int)
    score_rows["scoreAwayParsed"] = score_rows["scoreAway"].apply(safe_int)

    score_rows = score_rows[
        score_rows["scoreHomeParsed"].notna()
        & score_rows["scoreAwayParsed"].notna()
    ].copy()

    return score_rows


def get_final_score_from_pbp(pbp_df: pd.DataFrame) -> tuple[int, int]:
    """
    Final score is the last valid score row in play-by-play.
    """
    valid_score_rows = get_valid_score_rows(pbp_df)

    if valid_score_rows.empty:
        raise ValueError("No valid scoring rows found.")

    final_row = valid_score_rows.iloc[-1]

    final_home_score = int(final_row["scoreHomeParsed"])
    final_away_score = int(final_row["scoreAwayParsed"])

    return final_home_score, final_away_score


def backfill_game(db, game_id: str) -> int:
    """
    Fetch one game's play-by-play and insert one training row per unique score state.
    """
    pbp = playbyplayv3.PlayByPlayV3(
        game_id=game_id,
        start_period=1,
        end_period=10,
    )

    pbp_df = pbp.get_data_frames()[0]

    if pbp_df.empty:
        print(f"No play-by-play found for {game_id}")
        return 0

    final_home_score, final_away_score = get_final_score_from_pbp(pbp_df)

    scoring_rows = get_valid_score_rows(pbp_df)

    inserted = 0
    previous_home_score = None
    previous_away_score = None

    for _, row in scoring_rows.iterrows():
        home_score = int(row["scoreHomeParsed"])
        away_score = int(row["scoreAwayParsed"])

        # Skip duplicate score states.
        if (
            previous_home_score == home_score
            and previous_away_score == away_score
        ):
            continue

        previous_home_score = home_score
        previous_away_score = away_score

        period = int(row["period"])
        clock = nba_clock_to_mmss(row["clock"])

        row_created = create_historical_game_state(
            db=db,
            game_id=game_id,
            home_team="Home Team",
            away_team="Away Team",
            home_score=home_score,
            away_score=away_score,
            period=period,
            clock=clock,
            final_home_score=final_home_score,
            final_away_score=final_away_score,
        )

        if row_created is not None:
            inserted += 1
    
    db.commit()
    return inserted


def main():
    game_ids = get_completed_game_ids(SEASON, MAX_GAMES)

    print(f"Found {len(game_ids)} games.")

    total_inserted = 0

    for game_id in game_ids:
        print(f"Backfilling game {game_id}...")

        db = session_local()

        try:
            inserted = backfill_game(db, game_id)
            total_inserted += inserted
            print(f"Inserted {inserted} rows for {game_id}.")
            print(f"Total inserted so far: {total_inserted}")

        except Exception as e:
            db.rollback()
            print(f"Failed on {game_id}: {e}")

        finally:
            db.close()

        time.sleep(REQUEST_SLEEP_SECONDS)

    print(f"Done. Inserted {total_inserted} historical game-state rows.")


if __name__ == "__main__":
    main()
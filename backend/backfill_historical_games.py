"""
Run this locally, not in Codespaces.

Codespaces/NBA.com may return 403 for nba_api.
This script uses nba_api locally to fetch historical NBA play-by-play,
convert it into game-state training rows, and upload those rows to Supabase.

This version:
- Uses PlayByPlayV3
- Inserts every play/event
- Carries forward score for non-scoring events
- Uses real home/away abbreviations
- Runs games in parallel
- Bulk inserts once per game
"""

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder, playbyplayv3

from db.session import session_local
from services.historical_data_service import bulk_create_historical_game_states
from services.prediction_service import (
    calculate_game_progress,
    calculate_home_win_probability,
    calculate_seconds_remaining,
)


SEASON = "2023-26"
SEASON_TYPE = "Regular Season"
MAX_GAMES = 1230

MAX_WORKERS = 1
REQUEST_SLEEP_SECONDS = 5


def safe_int(value):
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


def safe_float(value):
    if value is None:
        return None

    if pd.isna(value):
        return None

    if value == "":
        return None

    try:
        return float(value)
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


def get_completed_games(season: str, max_games: int) -> tuple[list[str], pd.DataFrame]:
    """
    Gets completed game IDs for a season.

    LeagueGameFinder returns one row per team per game,
    so GAME_ID appears twice. We drop duplicates.

    Also returns the full dataframe so we can infer home/away teams.
    """
    finder = leaguegamefinder.LeagueGameFinder(
        season_nullable=season,
        season_type_nullable=SEASON_TYPE,
        league_id_nullable="00",
        timeout=60,
    )

    games_df = finder.get_data_frames()[0]

    game_ids = games_df["GAME_ID"].drop_duplicates().head(max_games).tolist()

    return game_ids, games_df


def get_home_away_from_gamefinder(
    games_df: pd.DataFrame,
    game_id: str,
) -> tuple[str, str]:
    """
    Infer home and away team abbreviations from LeagueGameFinder.

    Home team row example:
        MATCHUP = "BOS vs. NYK"

    Away team row example:
        MATCHUP = "NYK @ BOS"
    """
    game_rows = games_df[games_df["GAME_ID"] == game_id]

    if game_rows.empty:
        return "UNK", "UNK"

    home_team_abbr = "UNK"
    away_team_abbr = "UNK"

    for _, row in game_rows.iterrows():
        team_abbr = row.get("TEAM_ABBREVIATION")
        matchup = row.get("MATCHUP")

        if not isinstance(matchup, str):
            continue

        if " vs. " in matchup:
            home_team_abbr = team_abbr

            parts = matchup.split(" vs. ")
            if len(parts) == 2:
                away_team_abbr = parts[1]

        elif " @ " in matchup:
            away_team_abbr = team_abbr

            parts = matchup.split(" @ ")
            if len(parts) == 2:
                home_team_abbr = parts[1]

    return home_team_abbr, away_team_abbr


def get_valid_score_rows(pbp_df: pd.DataFrame) -> pd.DataFrame:
    """
    Used only to determine final score.
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
    valid_score_rows = get_valid_score_rows(pbp_df)

    if valid_score_rows.empty:
        raise ValueError("No valid scoring rows found.")

    final_row = valid_score_rows.iloc[-1]

    final_home_score = int(final_row["scoreHomeParsed"])
    final_away_score = int(final_row["scoreAwayParsed"])

    return final_home_score, final_away_score


def build_rows_for_game(
    game_id: str,
    games_df: pd.DataFrame,
    pbp_df: pd.DataFrame,
) -> list[dict]:
    """
    Convert one game's play-by-play dataframe into database row dictionaries.

    This creates one row per play/event.
    Non-scoring events carry forward the most recent known score.
    """
    home_team_abbr, away_team_abbr = get_home_away_from_gamefinder(
        games_df=games_df,
        game_id=game_id,
    )

    final_home_score, final_away_score = get_final_score_from_pbp(pbp_df)
    home_team_won = 1 if final_home_score > final_away_score else 0

    rows_to_insert = []

    current_home_score = 0
    current_away_score = 0

    for _, row in pbp_df.iterrows():
        parsed_home_score = safe_int(row.get("scoreHome"))
        parsed_away_score = safe_int(row.get("scoreAway"))

        if parsed_home_score is not None and parsed_away_score is not None:
            current_home_score = parsed_home_score
            current_away_score = parsed_away_score

        period = safe_int(row.get("period"))

        if period is None:
            continue

        clock = nba_clock_to_mmss(row.get("clock"))
        action_number = safe_int(row.get("actionNumber"))

        if action_number is None:
            continue

        score_diff = current_home_score - current_away_score
        seconds_remaining = calculate_seconds_remaining(period, clock)
        game_progress = calculate_game_progress(period, clock)

        home_win_probability_baseline = calculate_home_win_probability(
            home_score=current_home_score,
            away_score=current_away_score,
            period=period,
            clock=clock,
        )

        rows_to_insert.append(
            {
                "game_id": game_id,
                "season": SEASON,
                "season_type": SEASON_TYPE,

                "home_team": home_team_abbr,
                "away_team": away_team_abbr,
                "home_team_abbr": home_team_abbr,
                "away_team_abbr": away_team_abbr,

                "home_score": current_home_score,
                "away_score": current_away_score,
                "score_diff": score_diff,

                "period": period,
                "clock": clock,
                "raw_clock": row.get("clock"),

                "seconds_remaining": seconds_remaining,
                "game_progress": game_progress,

                "action_number": action_number,
                "action_type": row.get("actionType"),
                "sub_type": row.get("subType"),
                "description": row.get("description"),

                "team_tricode": row.get("teamTricode"),
                "player_name": row.get("playerName"),

                "shot_value": safe_int(row.get("shotValue")),
                "shot_result": row.get("shotResult"),
                "is_field_goal": safe_int(row.get("isFieldGoal")),
                "shot_distance": safe_float(row.get("shotDistance")),

                "home_win_probability_baseline": home_win_probability_baseline,

                "final_home_score": final_home_score,
                "final_away_score": final_away_score,
                "home_team_won": home_team_won,
            }
        )

    return rows_to_insert


def backfill_game(db, game_id: str, games_df: pd.DataFrame) -> int:
    pbp = playbyplayv3.PlayByPlayV3(
        game_id=game_id,
        start_period=1,
        end_period=10,
        timeout=60,
    )

    pbp_df = pbp.get_data_frames()[0]

    if pbp_df.empty:
        print(f"No play-by-play found for {game_id}")
        return 0

    rows_to_insert = build_rows_for_game(
        game_id=game_id,
        games_df=games_df,
        pbp_df=pbp_df,
    )

    inserted = bulk_create_historical_game_states(db, rows_to_insert)

    return inserted


def process_game(game_id: str, games_df: pd.DataFrame) -> tuple[str, int, str | None]:
    db = session_local()

    try:
        inserted = backfill_game(db, game_id, games_df)
        return game_id, inserted, None

    except Exception as e:
        db.rollback()
        return game_id, 0, str(e)

    finally:
        db.close()


def main():
    game_ids, games_df = get_completed_games(SEASON, MAX_GAMES)

    print(f"Found {len(game_ids)} games.")
    print(f"Season: {SEASON}")
    print(f"Season type: {SEASON_TYPE}")
    print(f"Max games: {MAX_GAMES}")
    print(f"Max workers: {MAX_WORKERS}")

    total_inserted = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_game_id = {
            executor.submit(process_game, game_id, games_df): game_id
            for game_id in game_ids
        }

        for future in as_completed(future_to_game_id):
            game_id = future_to_game_id[future]

            try:
                completed_game_id, inserted, error = future.result()

                if error:
                    print(f"Failed on {completed_game_id}: {error}")
                else:
                    total_inserted += inserted
                    print(
                        f"Inserted {inserted} rows for {completed_game_id}. "
                        f"Total inserted so far: {total_inserted}"
                    )

            except Exception as e:
                print(f"Unexpected failure on {game_id}: {e}")

            time.sleep(REQUEST_SLEEP_SECONDS)

    print(f"Done. Inserted {total_inserted} historical game-state rows.")


if __name__ == "__main__":
    main()
from __future__ import annotations

import argparse

import pandas as pd
from sqlalchemy import MetaData, Table
from sqlalchemy.dialects.postgresql import insert

from db.session import engine


STARTING_ELO = 1500.0
LEAGUE_AVERAGE_ELO = 1505.0
SEASON_CARRYOVER_WEIGHT = 0.75

BASE_K = 20.0
HOME_COURT_ADVANTAGE = 65.0


def regress_elo_to_mean(elo: float) -> float:
    return (
        SEASON_CARRYOVER_WEIGHT * elo
        + (1 - SEASON_CARRYOVER_WEIGHT) * LEAGUE_AVERAGE_ELO
    )


def expected_win_probability(team_elo: float, opponent_elo: float) -> float:
    return 1 / (1 + 10 ** ((opponent_elo - team_elo) / 400))


def margin_adjusted_k_factor(
    margin_of_victory: int,
    winner_elo_diff: float,
) -> float:
    return (
        BASE_K
        * ((margin_of_victory + 3) ** 0.8)
        / (7.5 + 0.006 * winner_elo_diff)
    )


def update_home_away_elo(
    home_elo: float,
    away_elo: float,
    home_score: int,
    away_score: int,
) -> tuple[float, float, float, float, float]:
    adjusted_home_elo = home_elo + HOME_COURT_ADVANTAGE

    expected_home = expected_win_probability(adjusted_home_elo, away_elo)
    expected_away = 1 - expected_home

    home_won = home_score > away_score
    margin_of_victory = abs(home_score - away_score)

    if home_won:
        winner_elo_diff = home_elo - away_elo
    else:
        winner_elo_diff = away_elo - home_elo

    k = margin_adjusted_k_factor(
        margin_of_victory=margin_of_victory,
        winner_elo_diff=winner_elo_diff,
    )

    actual_home = 1.0 if home_won else 0.0
    actual_away = 1.0 - actual_home

    new_home_elo = home_elo + k * (actual_home - expected_home)
    new_away_elo = away_elo + k * (actual_away - expected_away)

    return new_home_elo, new_away_elo, expected_home, expected_away, k


def read_games_for_season(season: str) -> pd.DataFrame:
    query = """
        SELECT
            nba_game_id,
            season,
            season_type,
            game_date,
            home_team_id,
            away_team_id,
            home_team_name,
            away_team_name,
            home_score,
            away_score,
            home_win
        FROM games
        WHERE season = %(season)s
          AND home_score IS NOT NULL
          AND away_score IS NOT NULL
        ORDER BY
            CASE
                WHEN season_type = 'Regular Season' THEN 1
                WHEN season_type = 'Playoffs' THEN 2
                ELSE 3
            END,
            game_date ASC,
            nba_game_id ASC
    """

    return pd.read_sql(query, engine, params={"season": season})


def read_games_for_seasons(seasons: list[str]) -> pd.DataFrame:
    query = """
        SELECT
            nba_game_id,
            season,
            season_type,
            game_date,
            home_team_id,
            away_team_id,
            home_team_name,
            away_team_name,
            home_score,
            away_score,
            home_win
        FROM games
        WHERE season = ANY(%(seasons)s)
          AND home_score IS NOT NULL
          AND away_score IS NOT NULL
        ORDER BY
            season ASC,
            CASE
                WHEN season_type = 'Regular Season' THEN 1
                WHEN season_type = 'Playoffs' THEN 2
                ELSE 3
            END,
            game_date ASC,
            nba_game_id ASC
    """

    return pd.read_sql(query, engine, params={"seasons": seasons})


def calculate_rest_features(
    game_date: pd.Timestamp,
    home_team_id: str,
    away_team_id: str,
    last_game_date_by_team: dict[str, pd.Timestamp],
) -> dict:
    home_previous_game_date = last_game_date_by_team.get(home_team_id)
    away_previous_game_date = last_game_date_by_team.get(away_team_id)

    home_days_rest = (
        (game_date.date() - home_previous_game_date.date()).days
        if home_previous_game_date is not None
        else None
    )

    away_days_rest = (
        (game_date.date() - away_previous_game_date.date()).days
        if away_previous_game_date is not None
        else None
    )

    rest_diff = (
        home_days_rest - away_days_rest
        if home_days_rest is not None and away_days_rest is not None
        else None
    )

    return {
        "home_days_rest": home_days_rest,
        "away_days_rest": away_days_rest,
        "rest_diff": rest_diff,
        "home_back_to_back": home_days_rest == 1,
        "away_back_to_back": away_days_rest == 1,
    }


def build_team_elo_rows(
    games_df: pd.DataFrame,
    current_team_elos: dict[str, float] | None = None,
    last_game_date_by_team: dict[str, pd.Timestamp] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float], dict[str, pd.Timestamp]]:
    if current_team_elos is None:
        current_team_elos = {}

    if last_game_date_by_team is None:
        last_game_date_by_team = {}

    team_elo_rows = []
    strength_rows = []

    for _, game in games_df.iterrows():
        nba_game_id = str(game["nba_game_id"])
        season = str(game["season"])
        season_type = str(game["season_type"])
        game_date = pd.to_datetime(game["game_date"])

        home_team_id = str(game["home_team_id"])
        away_team_id = str(game["away_team_id"])

        home_score = int(game["home_score"])
        away_score = int(game["away_score"])

        pregame_home_elo = current_team_elos.get(home_team_id, STARTING_ELO)
        pregame_away_elo = current_team_elos.get(away_team_id, STARTING_ELO)

        rest_features = calculate_rest_features(
            game_date=game_date,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            last_game_date_by_team=last_game_date_by_team,
        )

        (
            postgame_home_elo,
            postgame_away_elo,
            expected_home,
            expected_away,
            k,
        ) = update_home_away_elo(
            home_elo=pregame_home_elo,
            away_elo=pregame_away_elo,
            home_score=home_score,
            away_score=away_score,
        )

        actual_home = 1.0 if home_score > away_score else 0.0
        actual_away = 1.0 - actual_home

        team_elo_rows.append(
            {
                "nba_game_id": nba_game_id,
                "nba_team_id": home_team_id,
                "opponent_team_id": away_team_id,
                "season": season,
                "season_type": season_type,
                "game_date": game_date,
                "is_home": True,
                "pregame_elo": pregame_home_elo,
                "postgame_elo": postgame_home_elo,
                "expected_win_probability": expected_home,
                "actual_result": actual_home,
                "k_factor": k,
                "home_court_adjustment": HOME_COURT_ADVANTAGE,
            }
        )

        team_elo_rows.append(
            {
                "nba_game_id": nba_game_id,
                "nba_team_id": away_team_id,
                "opponent_team_id": home_team_id,
                "season": season,
                "season_type": season_type,
                "game_date": game_date,
                "is_home": False,
                "pregame_elo": pregame_away_elo,
                "postgame_elo": postgame_away_elo,
                "expected_win_probability": expected_away,
                "actual_result": actual_away,
                "k_factor": k,
                "home_court_adjustment": 0.0,
            }
        )

        home_availability_adjustment = 0.0
        away_availability_adjustment = 0.0

        adjusted_home_rating = pregame_home_elo + home_availability_adjustment
        adjusted_away_rating = pregame_away_elo + away_availability_adjustment

        strength_rows.append(
            {
                "nba_game_id": nba_game_id,
                "season": season,
                "season_type": season_type,
                "home_team_id": home_team_id,
                "away_team_id": away_team_id,
                "pregame_home_elo": pregame_home_elo,
                "pregame_away_elo": pregame_away_elo,
                "home_availability_adjustment": home_availability_adjustment,
                "away_availability_adjustment": away_availability_adjustment,
                "adjusted_home_rating": adjusted_home_rating,
                "adjusted_away_rating": adjusted_away_rating,
                "team_rating_diff": adjusted_home_rating - adjusted_away_rating,
                "home_days_rest": rest_features["home_days_rest"],
                "away_days_rest": rest_features["away_days_rest"],
                "rest_diff": rest_features["rest_diff"],
                "home_back_to_back": rest_features["home_back_to_back"],
                "away_back_to_back": rest_features["away_back_to_back"],
            }
        )

        current_team_elos[home_team_id] = postgame_home_elo
        current_team_elos[away_team_id] = postgame_away_elo

        last_game_date_by_team[home_team_id] = game_date
        last_game_date_by_team[away_team_id] = game_date

    return (
        pd.DataFrame(team_elo_rows),
        pd.DataFrame(strength_rows),
        current_team_elos,
        last_game_date_by_team,
    )


from sqlalchemy import MetaData, Table
from sqlalchemy.dialects.postgresql import insert

from db.session import engine


def clean_records_for_postgres(df: pd.DataFrame) -> list[dict]:
    cleaned_df = df.astype(object).where(pd.notna(df), None)
    return cleaned_df.to_dict(orient="records")


def upsert_dataframe(
    df: pd.DataFrame,
    table_name: str,
    conflict_columns: list[str],
    batch_size: int = 250,
) -> int:
    if df.empty:
        return 0

    print(
        f"Upserting table={table_name}, rows={len(df)}, batch_size={batch_size}"
    )

    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)

    records = clean_records_for_postgres(df)

    total_count = 0

    for start in range(0, len(records), batch_size):
        end = min(start + batch_size, len(records))
        batch = records[start:end]

        print(f"  Batch {start}-{end} into {table_name}")

        stmt = insert(table).values(batch)

        update_columns = {
            column.name: getattr(stmt.excluded, column.name)
            for column in table.columns
            if column.name not in conflict_columns
            and column.name != "id"
            and column.name != "created_at"
        }

        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_columns,
            set_=update_columns,
        )

        with engine.begin() as connection:
            result = connection.execute(stmt)
            total_count += result.rowcount

    return total_count


def load_teams(teams_df) -> int:
    return upsert_dataframe(
        df=teams_df,
        table_name="teams",
        conflict_columns=["nba_team_id"],
    )


def load_games(games_df) -> int:
    return upsert_dataframe(
        df=games_df,
        table_name="games",
        conflict_columns=["nba_game_id"],
    )


def build_and_load_team_elo_for_season(season: str) -> None:
    print(f"Reading games for season={season}")
    games_df = read_games_for_season(season)

    if games_df.empty:
        print(f"No games found for season={season}")
        return

    print(f"Building Elo rows for {len(games_df)} games")

    (
        team_elo_df,
        strengths_df,
        _,
        _,
    ) = build_team_elo_rows(games_df)

    print(f"Loading {len(team_elo_df)} rows into team_elos")
    team_elo_count = upsert_dataframe(
        df=team_elo_df,
        table_name="team_elos",
        conflict_columns=["nba_game_id", "nba_team_id"],
    )

    print(f"Loading {len(strengths_df)} rows into game_team_strengths")
    strengths_count = upsert_dataframe(
        df=strengths_df,
        table_name="game_team_strengths",
        conflict_columns=["nba_game_id"],
    )

    print(
        f"Done season={season}: "
        f"team_elos={team_elo_count}, "
        f"game_team_strengths={strengths_count}"
    )


def build_and_load_team_elo_for_seasons(seasons: list[str]) -> None:
    all_team_elo_frames = []
    all_strength_frames = []

    current_team_elos: dict[str, float] = {}
    last_game_date_by_team: dict[str, pd.Timestamp] = {}

    for season in seasons:
        print(f"Reading games for season={season}")
        games_df = read_games_for_season(season)

        if games_df.empty:
            print(f"No games found for season={season}")
            continue

        print(f"Building Elo rows for {len(games_df)} games in {season}")

        (
            team_elo_df,
            strengths_df,
            current_team_elos,
            last_game_date_by_team,
        ) = build_team_elo_rows(
            games_df=games_df,
            current_team_elos=current_team_elos,
            last_game_date_by_team=last_game_date_by_team,
        )

        all_team_elo_frames.append(team_elo_df)
        all_strength_frames.append(strengths_df)

        current_team_elos = {
            team_id: regress_elo_to_mean(elo)
            for team_id, elo in current_team_elos.items()
        }

        # Reset rest tracking after the full season, including playoffs.
        last_game_date_by_team = {}

        print(f"Applied offseason Elo regression after {season}")

    if not all_team_elo_frames:
        print("No Elo rows built")
        return

    all_team_elos_df = pd.concat(all_team_elo_frames, ignore_index=True)
    all_strengths_df = pd.concat(all_strength_frames, ignore_index=True)

    print(f"Loading {len(all_team_elos_df)} rows into team_elos")
    team_elo_count = upsert_dataframe(
        df=all_team_elos_df,
        table_name="team_elos",
        conflict_columns=["nba_game_id", "nba_team_id"],
    )

    print(f"Loading {len(all_strengths_df)} rows into game_team_strengths")
    strengths_count = upsert_dataframe(
        df=all_strengths_df,
        table_name="game_team_strengths",
        conflict_columns=["nba_game_id"],
    )

    print(
        f"Done seasons={seasons}: "
        f"team_elos={team_elo_count}, "
        f"game_team_strengths={strengths_count}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", help="Example: 2024-25")
    parser.add_argument(
        "--seasons",
        nargs="+",
        help="Example: 2022-23 2023-24 2024-25 2025-26",
    )
    args = parser.parse_args()

    if args.seasons:
        build_and_load_team_elo_for_seasons(args.seasons)
    elif args.season:
        build_and_load_team_elo_for_season(args.season)
    else:
        raise ValueError("Provide either --season or --seasons")


if __name__ == "__main__":
    main()
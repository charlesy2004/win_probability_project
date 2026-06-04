from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text

from db.session import engine
from services.espn_service import get_live_games


ESPN_TO_NBA_ABBR = {
    "SA": "SAS",
    "NY": "NYK",
    "GS": "GSW",
    "NO": "NOP",
    "PHO": "PHX",
    "UTAH": "UTA",
}


def normalize_abbreviation(abbreviation: str | None) -> str | None:
    if not abbreviation:
        return None

    abbreviation = abbreviation.upper().strip()
    return ESPN_TO_NBA_ABBR.get(abbreviation, abbreviation)


def parse_game_date(date_value: str | None) -> datetime:
    if not date_value:
        return datetime.now(timezone.utc)

    return datetime.fromisoformat(date_value.replace("Z", "+00:00"))


def get_team_id(connection, abbreviation: str | None, display_name: str | None) -> str | None:
    nba_abbr = normalize_abbreviation(abbreviation)

    query = text(
        """
        SELECT nba_team_id
        FROM teams
        WHERE abbreviation = :abbreviation
           OR LOWER(display_name) = LOWER(:display_name)
        LIMIT 1
        """
    )

    row = connection.execute(
        query,
        {
            "abbreviation": nba_abbr,
            "display_name": display_name,
        },
    ).mappings().first()

    if row is None:
        return None

    return str(row["nba_team_id"])


def get_latest_team_elo(connection, team_id: str) -> float:
    query = text(
        """
        SELECT postgame_elo
        FROM team_elos
        WHERE nba_team_id = :team_id
          AND postgame_elo IS NOT NULL
        ORDER BY game_date DESC
        LIMIT 1
        """
    )

    row = connection.execute(query, {"team_id": team_id}).mappings().first()

    if row is None:
        return 1500.0

    return float(row["postgame_elo"])


def get_previous_game_date(connection, team_id: str, current_game_date: datetime):
    query = text(
        """
        SELECT game_date
        FROM games
        WHERE game_date < :current_game_date
          AND home_score IS NOT NULL
          AND away_score IS NOT NULL
          AND (
              home_team_id = :team_id
              OR away_team_id = :team_id
          )
        ORDER BY game_date DESC
        LIMIT 1
        """
    )

    row = connection.execute(
        query,
        {
            "team_id": team_id,
            "current_game_date": current_game_date,
        },
    ).mappings().first()

    if row is None:
        return None

    return row["game_date"]


def calculate_days_rest(connection, team_id: str, game_date: datetime) -> int:
    previous_game_date = get_previous_game_date(
        connection=connection,
        team_id=team_id,
        current_game_date=game_date,
    )

    if previous_game_date is None:
        return 0

    return max((game_date.date() - previous_game_date.date()).days, 0)


def upsert_live_game_strength(
    connection,
    espn_game_id: str,
    game_date: datetime,
    home_team_id: str,
    away_team_id: str,
    home_elo: float,
    away_elo: float,
    home_days_rest: int,
    away_days_rest: int,
) -> None:
    rest_diff = home_days_rest - away_days_rest

    query = text(
        """
        INSERT INTO game_team_strengths (
            nba_game_id,
            espn_game_id,
            season,
            season_type,
            home_team_id,
            away_team_id,
            pregame_home_elo,
            pregame_away_elo,
            home_availability_adjustment,
            away_availability_adjustment,
            adjusted_home_rating,
            adjusted_away_rating,
            team_rating_diff,
            home_days_rest,
            away_days_rest,
            rest_diff,
            home_back_to_back,
            away_back_to_back
        )
        VALUES (
            :nba_game_id,
            :espn_game_id,
            :season,
            :season_type,
            :home_team_id,
            :away_team_id,
            :pregame_home_elo,
            :pregame_away_elo,
            0.0,
            0.0,
            :adjusted_home_rating,
            :adjusted_away_rating,
            :team_rating_diff,
            :home_days_rest,
            :away_days_rest,
            :rest_diff,
            :home_back_to_back,
            :away_back_to_back
        )
        ON CONFLICT (nba_game_id)
        DO UPDATE SET
            espn_game_id = EXCLUDED.espn_game_id,
            home_team_id = EXCLUDED.home_team_id,
            away_team_id = EXCLUDED.away_team_id,
            pregame_home_elo = EXCLUDED.pregame_home_elo,
            pregame_away_elo = EXCLUDED.pregame_away_elo,
            adjusted_home_rating = EXCLUDED.adjusted_home_rating,
            adjusted_away_rating = EXCLUDED.adjusted_away_rating,
            team_rating_diff = EXCLUDED.team_rating_diff,
            home_days_rest = EXCLUDED.home_days_rest,
            away_days_rest = EXCLUDED.away_days_rest,
            rest_diff = EXCLUDED.rest_diff,
            home_back_to_back = EXCLUDED.home_back_to_back,
            away_back_to_back = EXCLUDED.away_back_to_back
        """
    )

    connection.execute(
        query,
        {
            "nba_game_id": f"espn:{espn_game_id}",
            "espn_game_id": espn_game_id,
            "season": "live",
            "season_type": "Live",
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "pregame_home_elo": home_elo,
            "pregame_away_elo": away_elo,
            "adjusted_home_rating": home_elo,
            "adjusted_away_rating": away_elo,
            "team_rating_diff": home_elo - away_elo,
            "home_days_rest": home_days_rest,
            "away_days_rest": away_days_rest,
            "rest_diff": rest_diff,
            "home_back_to_back": home_days_rest == 1,
            "away_back_to_back": away_days_rest == 1,
        },
    )


def prepare_live_game_strengths() -> None:
    games = get_live_games()

    print(f"Preparing live game strengths for {len(games)} games")

    prepared_count = 0
    skipped_count = 0

    with engine.begin() as connection:
        for game in games:
            espn_game_id = str(game["game_id"])
            game_date = parse_game_date(game.get("date"))

            home_team_id = get_team_id(
                connection=connection,
                abbreviation=game.get("home_team_abbr"),
                display_name=game.get("home_team"),
            )

            away_team_id = get_team_id(
                connection=connection,
                abbreviation=game.get("away_team_abbr"),
                display_name=game.get("away_team"),
            )

            if home_team_id is None or away_team_id is None:
                print(
                    f"Skipping game_id={espn_game_id}: "
                    f"home_team_id={home_team_id}, away_team_id={away_team_id}"
                )
                skipped_count += 1
                continue

            home_elo = get_latest_team_elo(connection, home_team_id)
            away_elo = get_latest_team_elo(connection, away_team_id)

            home_days_rest = calculate_days_rest(
                connection=connection,
                team_id=home_team_id,
                game_date=game_date,
            )

            away_days_rest = calculate_days_rest(
                connection=connection,
                team_id=away_team_id,
                game_date=game_date,
            )

            upsert_live_game_strength(
                connection=connection,
                espn_game_id=espn_game_id,
                game_date=game_date,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                home_elo=home_elo,
                away_elo=away_elo,
                home_days_rest=home_days_rest,
                away_days_rest=away_days_rest,
            )

            print(
                f"Prepared game_id={espn_game_id}: "
                f"{game.get('away_team')} @ {game.get('home_team')}, "
                f"home_elo={home_elo:.1f}, away_elo={away_elo:.1f}, "
                f"home_rest={home_days_rest}, away_rest={away_days_rest}"
            )

            prepared_count += 1

    print(
        f"Done preparing live game strengths: "
        f"prepared={prepared_count}, skipped={skipped_count}"
    )


def main() -> None:
    prepare_live_game_strengths()


if __name__ == "__main__":
    main()
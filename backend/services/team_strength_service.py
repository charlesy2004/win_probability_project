from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_game_team_strength_features(
    db: Session,
    game_id: str,
) -> dict | None:
    query = text(
        """
        SELECT
            pregame_home_elo,
            pregame_away_elo,
            team_rating_diff,
            home_days_rest,
            away_days_rest,
            rest_diff,
            home_back_to_back,
            away_back_to_back
        FROM game_team_strengths
        WHERE espn_game_id = :game_id
           OR nba_game_id = :game_id
        LIMIT 1
        """
    )

    row = db.execute(query, {"game_id": str(game_id)}).mappings().first()

    if row is None:
        return None

    return {
        "pregame_home_elo": float(row["pregame_home_elo"] or 1500.0),
        "pregame_away_elo": float(row["pregame_away_elo"] or 1500.0),
        "team_rating_diff": float(row["team_rating_diff"] or 0.0),
        "home_days_rest": int(row["home_days_rest"] or 0),
        "away_days_rest": int(row["away_days_rest"] or 0),
        "rest_diff": int(row["rest_diff"] or 0),
        "home_back_to_back": int(bool(row["home_back_to_back"])),
        "away_back_to_back": int(bool(row["away_back_to_back"])),
    }
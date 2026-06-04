from __future__ import annotations

from sqlalchemy.orm import Session

from services.game_state_feature_service import (
    build_live_model_features,
    calculate_baseline_probability,
)
from services.team_strength_service import get_game_team_strength_features
from services.win_probability_model_service import predict_home_win_probability


def get_live_home_win_probability(
    db: Session,
    game: dict,
) -> tuple[float, str]:
    game_id = str(game.get("game_id"))

    home_score = int(game.get("home_score") or 0)
    away_score = int(game.get("away_score") or 0)
    period = int(game.get("period") or 0)
    clock = game.get("clock")

    team_strength_features = get_game_team_strength_features(
        db=db,
        game_id=game_id,
    )

    if team_strength_features is None:
        probability = calculate_baseline_probability(
            home_score=home_score,
            away_score=away_score,
            period=period,
            clock=clock,
        )
        return probability, "baseline_fallback_missing_team_strength"

    try:
        model_features = build_live_model_features(
            home_score=home_score,
            away_score=away_score,
            period=period,
            clock=clock,
            team_strength_features=team_strength_features,
        )

        probability = predict_home_win_probability(model_features)
        return probability, "neural_network_v1"

    except Exception as error:
        print(f"Neural network prediction failed for game_id={game_id}: {error}")

        probability = calculate_baseline_probability(
            home_score=home_score,
            away_score=away_score,
            period=period,
            clock=clock,
        )
        return probability, "baseline_fallback_model_error"
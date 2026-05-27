from sqlalchemy.orm import Session

from db.models import HistoricalGameState
from services.prediction_service import (
    calculate_game_progress,
    calculate_home_win_probability,
    calculate_seconds_remaining,
)


def create_historical_game_state(
    db: Session,
    game_id: str,
    home_team: str,
    away_team: str,
    home_score: int,
    away_score: int,
    period: int,
    clock: str,
    final_home_score: int,
    final_away_score: int,
) -> HistoricalGameState | None:
    existing_row = (
        db.query(HistoricalGameState)
        .filter(HistoricalGameState.game_id == game_id)
        .filter(HistoricalGameState.period == period)
        .filter(HistoricalGameState.clock == clock)
        .filter(HistoricalGameState.home_score == home_score)
        .filter(HistoricalGameState.away_score == away_score)
        .first()
    )

    if existing_row:
        return None

    score_diff = home_score - away_score
    seconds_remaining = calculate_seconds_remaining(period, clock)
    game_progress = calculate_game_progress(period, clock)

    home_win_probability_baseline = calculate_home_win_probability(
        home_score=home_score,
        away_score=away_score,
        period=period,
        clock=clock,
    )

    home_team_won = 1 if final_home_score > final_away_score else 0

    row = HistoricalGameState(
        game_id=game_id,
        home_team=home_team,
        away_team=away_team,
        home_score=home_score,
        away_score=away_score,
        score_diff=score_diff,
        period=period,
        clock=clock,
        seconds_remaining=seconds_remaining,
        game_progress=game_progress,
        home_win_probability_baseline=home_win_probability_baseline,
        final_home_score=final_home_score,
        final_away_score=final_away_score,
        home_team_won=home_team_won,
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    return row
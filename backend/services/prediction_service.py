import math
import os
import joblib
import pandas as pd


def sigmoid(x: float) -> float:
    """Convert a raw model score into a probability between 0 and 1."""
    return 1 / (1 + math.exp(-x))


def parse_clock_to_seconds(clock: str) -> int:
    """
    Convert ESPN clock string into seconds remaining in the current period.

    Examples:
    "6:00" -> 360
    "0.0" -> 0
    "" -> 0
    """
    if not clock or clock == "0.0":
        return 0

    if ":" not in clock:
        return 0

    minutes, seconds = clock.split(":")
    return int(minutes) * 60 + int(float(seconds))


def calculate_home_win_probability_baseline(
    home_score: int,
    away_score: int,
    period: int,
    clock: str,
) -> float:
    """
    Simple baseline home win probability.

    This is not a trained ML model yet.
    It uses:
    - score difference
    - game progress
    - small home-court advantage
    """

    # Pregame / scheduled game
    if period == 0:
        return 0.52

    score_diff = home_score - away_score
    seconds_remaining_current_period = parse_clock_to_seconds(clock)

    # NBA game = 4 periods * 12 minutes * 60 seconds
    total_game_seconds = 48 * 60

    # Elapsed time before current period
    elapsed_before_period = max(period - 1, 0) * 12 * 60

    # Elapsed time inside current period
    elapsed_current_period = 12 * 60 - seconds_remaining_current_period

    elapsed_seconds = elapsed_before_period + elapsed_current_period

    game_progress = min(max(elapsed_seconds / total_game_seconds, 0), 1)

    # Score difference should matter more later in the game
    score_weight = 0.08 + 0.18 * game_progress

    # Small home-court advantage
    home_court_bump = 0.08

    raw_score = home_court_bump + score_weight * score_diff

    probability = sigmoid(raw_score)

    return round(probability, 3)
    

def get_period_length_seconds(period: int) -> int:
    """
    NBA regulation periods are 12 minutes.
    Overtime periods are 5 minutes.
    """
    if period <= 4:
        return 12 * 60

    return 5 * 60


def calculate_total_game_seconds_through_period(period: int) -> int:
    """
    Total scheduled seconds through the end of the current period.

    Q1-Q4:
        period 1 end = 720
        period 2 end = 1440
        period 3 end = 2160
        period 4 end = 2880

    OT:
        period 5 end = 3180
        period 6 end = 3480
        etc.
    """
    if period <= 4:
        return period * 12 * 60

    regulation_seconds = 4 * 12 * 60
    overtime_periods_through_current = period - 4

    return regulation_seconds + overtime_periods_through_current * 5 * 60


def calculate_elapsed_seconds(period: int, clock: str) -> int:
    """
    Calculate elapsed game seconds from period and clock.

    Example:
    Q3 6:00:
        elapsed before Q3 = 24 minutes
        elapsed in Q3 = 6 minutes
        total elapsed = 30 minutes = 1800 seconds

    OT 3:00:
        elapsed before OT = 48 minutes
        elapsed in OT = 2 minutes
        total elapsed = 50 minutes = 3000 seconds
    """
    if period == 0:
        return 0

    seconds_left_in_period = parse_clock_to_seconds(clock)
    period_length = get_period_length_seconds(period)

    elapsed_in_current_period = period_length - seconds_left_in_period
    elapsed_in_current_period = max(elapsed_in_current_period, 0)

    if period <= 4:
        elapsed_before_period = (period - 1) * 12 * 60
    else:
        regulation_seconds = 4 * 12 * 60
        completed_overtime_periods = period - 5
        elapsed_before_period = regulation_seconds + completed_overtime_periods * 5 * 60

    return elapsed_before_period + elapsed_in_current_period


def calculate_seconds_remaining(period: int, clock: str) -> int:
    """
    Calculate seconds remaining in the scheduled game length.

    In regulation:
        Q1-Q4 assume 48 minutes total.

    In overtime:
        Each overtime period adds 5 minutes to total possible game length.
        For period 5, total game length is 53 minutes.
        For period 6, total game length is 58 minutes.
    """
    if period == 0:
        return 48 * 60

    elapsed_seconds = calculate_elapsed_seconds(period, clock)
    total_seconds_through_current_period = calculate_total_game_seconds_through_period(period)

    seconds_remaining = total_seconds_through_current_period - elapsed_seconds

    return max(seconds_remaining, 0)


def calculate_game_progress(period: int, clock: str) -> float:
    """
    Game progress between 0 and 1.

    Regulation is based on 48 minutes.
    Overtime extends the denominator to include the current OT period.
    """
    if period == 0:
        return 0.0

    elapsed_seconds = calculate_elapsed_seconds(period, clock)
    total_seconds_through_current_period = calculate_total_game_seconds_through_period(period)

    progress = elapsed_seconds / total_seconds_through_current_period

    return round(min(max(progress, 0), 1), 3)


MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "models",
    "win_probability_model.pkl",
)

_model_bundle = None


def load_win_probability_model():
    global _model_bundle

    if _model_bundle is None:
        _model_bundle = joblib.load(MODEL_PATH)

    return _model_bundle

def calculate_home_win_probability(
    home_score: int,
    away_score: int,
    period: int,
    clock: str,
) -> float:
    try:
        bundle = load_win_probability_model()
        model = bundle["model"]
        feature_columns = bundle["feature_columns"]

        score_diff = home_score - away_score
        seconds_remaining = calculate_seconds_remaining(period, clock)
        game_progress = calculate_game_progress(period, clock)

        features = pd.DataFrame(
            [
                {
                    "score_diff": score_diff,
                    "seconds_remaining": seconds_remaining,
                    "game_progress": game_progress,
                    "period": period,
                    "home_score": home_score,
                    "away_score": away_score,
                }
            ]
        )

        features = features[feature_columns]

        probability = model.predict_proba(features)[0][1]

        return round(float(probability), 3)

    except Exception as e:
        print(f"Model prediction failed. Using baseline fallback: {e}")

        return calculate_home_win_probability_baseline(
            home_score=home_score,
            away_score=away_score,
            period=period,
            clock=clock,
        )
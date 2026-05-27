import math

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


def calculate_home_win_probability(
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
    

def calculate_seconds_remaining(period: int, clock: str) -> int:
    if period == 0:
        return 48 * 60

    seconds_left_in_period = parse_clock_to_seconds(clock)

    periods_remaining_after_current = max(4 - period, 0)

    return seconds_left_in_period + periods_remaining_after_current * 12 * 60


def calculate_game_progress(period: int, clock: str) -> float:
    total_game_seconds = 48 * 60
    seconds_remaining = calculate_seconds_remaining(period, clock)

    progress = 1 - (seconds_remaining / total_game_seconds)

    return round(min(max(progress, 0), 1), 3)
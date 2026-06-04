from __future__ import annotations


def calculate_score_diff(home_score: int, away_score: int) -> int:
    return int(home_score or 0) - int(away_score or 0)


def calculate_seconds_remaining(period: int, clock: str | None) -> int:
    if period is None:
        return 0

    period = int(period)

    if not clock:
        minutes = 0
        seconds = 0
    else:
        try:
            minutes_str, seconds_str = clock.split(":")
            minutes = int(minutes_str)
            seconds = int(seconds_str)
        except ValueError:
            minutes = 0
            seconds = 0

    seconds_left_in_current_period = minutes * 60 + seconds

    # NBA regulation: 4 quarters, 12 minutes each.
    if period <= 4:
        future_periods = max(4 - period, 0)
        return future_periods * 12 * 60 + seconds_left_in_current_period

    # Overtime: keep it simple and only use current OT clock.
    return seconds_left_in_current_period


def calculate_game_progress(seconds_remaining: int) -> float:
    regulation_seconds = 48 * 60

    progress = 1 - (seconds_remaining / regulation_seconds)

    return max(0.0, min(1.0, progress))


def build_live_model_features(
    home_score: int,
    away_score: int,
    period: int,
    clock: str | None,
    team_strength_features: dict,
) -> dict:
    home_score = int(home_score or 0)
    away_score = int(away_score or 0)
    period = int(period or 0)

    seconds_remaining = calculate_seconds_remaining(
        period=period,
        clock=clock,
    )

    game_progress = calculate_game_progress(seconds_remaining)

    live_features = {
        "score_diff": calculate_score_diff(home_score, away_score),
        "seconds_remaining": seconds_remaining,
        "game_progress": game_progress,
        "period": period,
        "home_score": home_score,
        "away_score": away_score,
    }

    live_features.update(team_strength_features)

    return live_features


def calculate_baseline_probability(
    home_score: int,
    away_score: int,
    period: int,
    clock: str | None,
) -> float:
    home_score = int(home_score or 0)
    away_score = int(away_score or 0)
    period = int(period or 0)

    seconds_remaining = calculate_seconds_remaining(period, clock)
    game_progress = calculate_game_progress(seconds_remaining)
    score_diff = home_score - away_score

    # Temporary fallback only.
    # Higher score diff and later game progress increase probability.
    probability = 0.5 + (score_diff * 0.025) + ((game_progress - 0.5) * 0.10)

    return max(0.01, min(0.99, probability))
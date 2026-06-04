BASE_FEATURE_COLUMNS = [
    "score_diff",
    "seconds_remaining",
    "game_progress",
    "period",
    "home_score",
    "away_score",
]

TEAM_CONTEXT_FEATURE_COLUMNS = [
    "pregame_home_elo",
    "pregame_away_elo",
    "team_rating_diff",
    "home_days_rest",
    "away_days_rest",
    "rest_diff",
    "home_back_to_back",
    "away_back_to_back",
]

MODEL_FEATURE_COLUMNS = BASE_FEATURE_COLUMNS + TEAM_CONTEXT_FEATURE_COLUMNS

TARGET_COLUMN = "home_team_won"
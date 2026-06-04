import requests
# from services.prediction_service import calculate_home_win_probability

ESPN_SCOREBOARD_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
)
ESPN_CORE_NBA_BASE_URL = (
    "https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba"
)


def fetch_espn_scoreboard() -> dict:
    response = requests.get(ESPN_SCOREBOARD_URL, timeout=10)
    response.raise_for_status()
    return response.json()


def format_game(event: dict) -> dict:
    competition = event["competitions"][0]
    competitors = competition["competitors"]

    home = next(team for team in competitors if team["homeAway"] == "home")
    away = next(team for team in competitors if team["homeAway"] == "away")

    status_type = event["status"]["type"]

    odds_list = competition.get("odds", [])
    first_odds = odds_list[0] if odds_list else {}

    home_score = int(home.get("score", 0))
    away_score = int(away.get("score", 0))
    period = event["status"].get("period", 0)
    clock = event["status"].get("displayClock", "")

    return {
        "game_id": event.get("id"),
        "name": event.get("name"),
        "short_name": event.get("shortName"),
        "date": event.get("date"),

        "away_team": away["team"]["displayName"],
        "away_team_abbr": away["team"]["abbreviation"],
        "away_score": int(away.get("score", 0)),
        "away_record": away.get("record", ""),

        "home_team": home["team"]["displayName"],
        "home_team_abbr": home["team"]["abbreviation"],
        "home_score": int(home.get("score", 0)),
        "home_record": home.get("record", ""),

        "period": event["status"].get("period", 0),
        "clock": event["status"].get("displayClock", ""),
        "status": status_type.get("description", ""),
        "detail": status_type.get("detail", ""),

        "venue": competition.get("venue", {}).get("fullName", ""),
        "series": competition.get("series", {}).get("summary", ""),
        "broadcast": competition.get("broadcast", ""),

        "spread": first_odds.get("details", ""),
        "over_under": first_odds.get("overUnder", None),

        # Placeholder until actual model exists
        "home_win_probability": None,
        "model_type": None,
        "model_version": None,
            }


def get_live_games() -> list[dict]:
    data = fetch_espn_scoreboard()
    events = data.get("events", [])

    return [format_game(event) for event in events]

def get_game_by_id(game_id: str) -> dict | None:
    games = get_live_games()

    for game in games:
        if game["game_id"] == game_id:
            return game

    return None

def get_win_probability_timeline(game_id: str) -> dict:
    return {
        "game_id": game_id,
        "timeline": [
            {"time": "Q1 12:00", "home_win_probability": 0.50},
            {"time": "Q1 6:00", "home_win_probability": 0.52},
            {"time": "Q2 12:00", "home_win_probability": 0.48},
            {"time": "Q2 6:00", "home_win_probability": 0.55},
            {"time": "Q3 12:00", "home_win_probability": 0.60},
            {"time": "Q3 6:00", "home_win_probability": 0.58},
            {"time": "Q4 12:00", "home_win_probability": 0.65},
            {"time": "Q4 6:00", "home_win_probability": 0.62},
        ],
    }

def get_game_plays(game_id: str) -> list[dict]:
    url = (
        f"{ESPN_CORE_NBA_BASE_URL}/events/{game_id}/"
        f"competitions/{game_id}/plays?limit=1000"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()
    raw_plays = data.get("items", [])

    cleaned_plays = []

    for play in raw_plays:
        period = play.get("period", {}).get("number")
        clock = play.get("clock", {}).get("displayValue")

        home_score = play.get("homeScore")
        away_score = play.get("awayScore")

        cleaned_plays.append(
            {
                "id": play.get("id"),
                "sequence_number": play.get("sequenceNumber"),
                "period": period,
                "clock": clock,
                "text": play.get("text"),
                "short_text": play.get("shortText"),
                "type": play.get("type", {}).get("text"),
                "home_score": home_score,
                "away_score": away_score,
                "scoring_play": play.get("scoringPlay"),
                "score_value": play.get("scoreValue"),
                "shooting_play": play.get("shootingPlay"),
                "points_attempted": play.get("pointsAttempted"),
                "wallclock": play.get("wallclock"),
            }
        )
    cleaned_plays.sort(
        key=lambda play: int(play.get("sequence_number") or 0),
        reverse=True,
    )
    return cleaned_plays

def get_game_state_dashboard(game_id: str) -> dict:
    game = get_game_by_id(game_id)

    plays = get_game_plays(game_id)
    if game is None:
        return []
    latest_play = plays[-1] if plays else None

    home_score = game["home_score"]
    away_score = game["away_score"]
    score_diff = home_score - away_score
    period = game.get("period", 0)
    clock = game.get("clock", "0.0")
    possession_team = None
    if latest_play and latest_play["team"]:
        possession_team = latest_play.get("team")
    return {
        "game_id": game_id,
        "home_team": game["home_team"],
        "away_team": game["away_team"],
        "home_team_abbr": game["home_team_abbr"],
        "away_team_abbr": game["away_team_abbr"],
        "home_score": home_score,
        "away_score": away_score,
        "score_diff": score_diff,
        "period": period,
        "clock": clock,
        "possession_team": possession_team,
        "home_win_probability": game["home_win_probability"],

        # Placeholder for now. ESPN may not expose current-period team fouls cleanly.
        "home_fouls": None,
        "away_fouls": None,
        "home_in_bonus": False,
        "away_in_bonus": False,
    }
import requests


ESPN_SCOREBOARD_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
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
        "home_win_probability": 0.50,
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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI(title="NBA Win Probability API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "NBA Win Probability API is running!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/games/live")
def get_live_games():
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()
    events = data.get("events", [])

    formatted_games = []

    for event in events:
        competition = event["competitions"][0]
        competitors = competition["competitors"]

        home = next(team for team in competitors if team["homeAway"] == "home")
        away = next(team for team in competitors if team["homeAway"] == "away")

        status_type = event["status"]["type"]

        odds_list = competition.get("odds", [])
        first_odds = odds_list[0] if odds_list else {}

        formatted_games.append(
            {
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

                # Placeholder until we build the actual model
                "home_win_probability": 0.50,
            }
        )

    return formatted_games
    

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    # Placeholder for fetching live games data
    return [
            {
                "game_id": "001",
                "home_team": "Knicks",
                "away_team": "Celtics",
                "home_score": 98,
                "away_score": 94,
                "period": 4,
                "clock": "03:21",
                "home_win_probability": 0.71,
            },
            {
                "game_id": "002",
                "home_team": "Nuggets",
                "away_team": "Lakers",
                "home_score": 103,
                "away_score": 99,
                "period": 4,
                "clock": "01:48",
                "home_win_probability": 0.63,
            },
        ]

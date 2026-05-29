from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.espn_service import (
    get_live_games, 
    get_game_by_id, 
    get_win_probability_timeline, 
    get_game_plays, 
    get_game_state_dashboard
)
from db.session import session_local
from services.snapshot_service import save_scoreboard_snapshots, get_snapshots_for_game
from services.historical_data_service import create_historical_game_state
import asyncio
from contextlib import asynccontextmanager

SNAPSHOT_CAPTURE_INTERVAL_SECONDS = 60
def capture_scoreboard_snapshot_once() -> int:
    games = get_live_games()

    db = session_local()

    try:
        count = save_scoreboard_snapshots(db, games)
        print(f"Captured {count} scoreboard snapshots")
        return count
    finally:
        db.close()
    
async def capture_snapshot_loop():
    while True:
        try:
            await asyncio.to_thread(capture_scoreboard_snapshot_once)
        except Exception as e:
            print(f"Error capturing scoreboard snapshot: {e}")
        await asyncio.sleep(SNAPSHOT_CAPTURE_INTERVAL_SECONDS)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(capture_snapshot_loop())
    try:
        yield
    except asyncio.CancelledError:
        pass
    
app = FastAPI(title="NBA Win Probability API", lifespan=lifespan)
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
def live_games():
    return get_live_games()

@app.get("/games/{game_id}/win-probability")
def win_probability_timeline(game_id: str):
    db = session_local()

    try:
        timeline = get_snapshots_for_game(db, game_id)
    finally:
        db.close()

    if timeline:
        return {
            "game_id": game_id,
            "timeline": timeline,
            "source": "database",
        }

    return get_win_probability_timeline(game_id)

@app.get("/games/{game_id}/plays")
def game_plays(game_id: str):
    plays = get_game_plays(game_id)
    return {
        "game_id": game_id,
        "count": len(plays),
        "plays": plays,
    }

@app.get("/games/{game_id}/state")
def game_state_dashboard(game_id: str):
    state = get_game_state_dashboard(game_id)

    if not state:
        raise HTTPException(status_code=404, detail="Game not found")

    return state

@app.get("/games/{game_id}")
def game_detail(game_id: str):
    game = get_game_by_id(game_id)

    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    return game

@app.post("/games/snapshots")
def create_scoreboard_snapshots():
    count = capture_scoreboard_snapshot_once()
    return {
        "message": "Scoreboard snapshots saved",
        "count": count,
    }

@app.post("/debug/historical-sample")
def create_historical_sample():
    db = session_local()

    try:
        row = create_historical_game_state(
            db=db,
            game_id="sample_001",
            home_team="Boston Celtics",
            away_team="New York Knicks",
            home_score=82,
            away_score=77,
            period=3,
            clock="06:00",
            final_home_score=112,
            final_away_score=105,
        )

        return {
            "id": row.id,
            "game_id": row.game_id,
            "score_diff": row.score_diff,
            "seconds_remaining": row.seconds_remaining,
            "game_progress": row.game_progress,
            "home_win_probability_baseline": row.home_win_probability_baseline,
            "home_team_won": row.home_team_won,
        }
    finally:
        db.close()


@app.get("/games/demo")
def get_demo_games():
    return [
        {
            "game_id": "demo-001",
            "home_team": "BOS",
            "away_team": "NYK",
            "home_score": 104,
            "away_score": 98,
            "period": 4,
            "clock": "02:14",
            "status": "Demo",
            "home_win_probability": 0.78,
            "away_win_probability": 0.22,
        }
    ]


@app.get("/games/demo-001/win-probability")
def get_demo_win_probability():
    return {
        "timeline": [
            {"time": "12:00 Q1", "home_win_probability": 0.52, "away_win_probability": 0.48},
            {"time": "06:00 Q1", "home_win_probability": 0.57, "away_win_probability": 0.43},
            {"time": "12:00 Q2", "home_win_probability": 0.49, "away_win_probability": 0.51},
            {"time": "06:00 Q2", "home_win_probability": 0.61, "away_win_probability": 0.39},
            {"time": "12:00 Q3", "home_win_probability": 0.66, "away_win_probability": 0.34},
            {"time": "06:00 Q3", "home_win_probability": 0.71, "away_win_probability": 0.29},
            {"time": "12:00 Q4", "home_win_probability": 0.74, "away_win_probability": 0.26},
            {"time": "02:14 Q4", "home_win_probability": 0.78, "away_win_probability": 0.22},
        ]
    }


@app.get("/games/demo-001/plays")
def get_demo_plays():
    return {
        "plays": [
            {
                "period": 4,
                "clock": "03:42",
                "description": "NYK makes 3-pt jump shot",
                "home_score": 101,
                "away_score": 96,
                "home_win_probability": 0.69,
            },
            {
                "period": 4,
                "clock": "03:05",
                "description": "BOS defensive rebound",
                "home_score": 101,
                "away_score": 96,
                "home_win_probability": 0.72,
            },
            {
                "period": 4,
                "clock": "02:41",
                "description": "BOS makes layup",
                "home_score": 103,
                "away_score": 96,
                "home_win_probability": 0.80,
            },
            {
                "period": 4,
                "clock": "02:14",
                "description": "NYK makes free throws",
                "home_score": 104,
                "away_score": 98,
                "home_win_probability": 0.78,
            },
        ]
    }


@app.get("/games/demo-001/state")
def get_demo_game_state():
    return {
        "game_id": "demo-001",
        "period": 4,
        "clock": "02:14",
        "home_team": "BOS",
        "away_team": "NYK",
        "home_score": 104,
        "away_score": 98,
        "score_differential": 6,
        "possession": "BOS",
        "home_fouls": 4,
        "away_fouls": 6,
        "home_bonus": False,
        "away_bonus": True,
        "home_win_probability": 0.78,
        "away_win_probability": 0.22,
    }
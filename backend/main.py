from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.espn_service import (
    get_live_games, get_game_by_id, get_win_probability_timeline
)
from db.session import session_local
from services.snapshot_service import save_scoreboard_snapshots, get_snapshots_for_game

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

@app.get("/games/{game_id}")
def game_detail(game_id: str):
    game = get_game_by_id(game_id)

    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    return game

@app.post("/games/snapshots")
def create_scoreboard_snapshots():
    games = get_live_games()

    db = session_local()

    try:
        count = save_scoreboard_snapshots(db, games)
        return {
            "message": "Scoreboard snapshots saved",
            "count": count,
        }
    finally:
        db.close()

@app.get("/debug/snapshots")
def debug_snapshots():
    db = session_local()

    try:
        from db.models import ScoreboardSnapshot

        rows = db.query(ScoreboardSnapshot).all()

        return [
            {
                "id": row.id,
                "game_id": row.game_id,
                "home_team": row.home_team,
                "away_team": row.away_team,
                "home_score": row.home_score,
                "away_score": row.away_score,
                "home_win_probability": row.home_win_probability,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    finally:
        db.close()
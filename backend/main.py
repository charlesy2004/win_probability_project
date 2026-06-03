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
from db.models import ScoreboardSnapshot, HistoricalGameState
from services.cache_service import get_live_games_from_cache, get_game_plays_from_cache, get_game_from_cache

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
    
# async def capture_snapshot_loop():
#     while True:
#         try:
#             await asyncio.to_thread(capture_scoreboard_snapshot_once)
#         except Exception as e:
#             print(f"Error capturing scoreboard snapshot: {e}")
#         await asyncio.sleep(SNAPSHOT_CAPTURE_INTERVAL_SECONDS)

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     task = asyncio.create_task(capture_snapshot_loop())
#     try:
#         yield
#     except asyncio.CancelledError:
#         pass
    
app = FastAPI(title="NBA Win Probability API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
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

@app.get("/pipeline/status")
def pipeline_status():
    db = session_local()
    try:
        latest_snapshot = (
            db.query(ScoreboardSnapshot)
            .order_by(ScoreboardSnapshot.created_at.desc())
            .first()
        )
        snapshot_cnt = db.query(ScoreboardSnapshot).count()
        if not latest_snapshot:
            return {
                "status": "No snapshots captured yet",
                "ingestion_mode": "render background worker",
                "snapshot_count": 0,
                "latest_snapshot": None,
                "model_type": "xgboost",
                "model_version": "v1",
            }
        return {
            "status": "OK",
            "ingestion_mode": "render background worker",
            "snapshot_count": snapshot_cnt,
            "latest_snapshot": {
                "game_id": latest_snapshot.game_id,
                "period": latest_snapshot.period,
                "clock": latest_snapshot.clock,
                "seconds_remaining": latest_snapshot.seconds_remaining,
                "home_score": latest_snapshot.home_score,
                "away_score": latest_snapshot.away_score,
                "home_win_probability": latest_snapshot.home_win_probability,
                "created_at": latest_snapshot.created_at.isoformat(),
            },
            "model_type": latest_snapshot.model_type,
            "model_version": latest_snapshot.model_version,

        }

    finally:
        db.close()

@app.get("/games/live")
def live_games():
    cached_games = get_live_games_from_cache()

    if cached_games is not None:
        return cached_games

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
    cached_plays = get_game_plays_from_cache(game_id)

    if cached_plays is not None:
        return {
            "game_id": game_id,
            "count": len(cached_plays),
            "plays": cached_plays,
            "source": "redis",
        }

    plays = get_game_plays(game_id)

    return {
        "game_id": game_id,
        "count": len(plays),
        "plays": plays,
        "source": "espn",
    }

@app.get("/games/{game_id}/state")
def game_state_dashboard(game_id: str):
    game = get_game_from_cache(game_id)

    if not game:
        live_games = get_live_games_from_cache()

        if live_games:
            game = next(
                (g for g in live_games if str(g.get("game_id")) == str(game_id)),
                None,
            )

    if not game:
        try:
            live_games = get_live_games()
            game = next(
                (g for g in live_games if str(g.get("game_id")) == str(game_id)),
                None,
            )
        except Exception:
            game = None

    if not game:
        return {
            "game_id": game_id,
            "status": "unavailable",
            "message": "Game state not available",
        }

    home_score = int(game.get("home_score") or 0)
    away_score = int(game.get("away_score") or 0)

    return {
        "game_id": game_id,
        "period": game.get("period"),
        "clock": game.get("clock"),
        "status": game.get("status"),
        "home_team": game.get("home_team"),
        "away_team": game.get("away_team"),
        "home_score": home_score,
        "away_score": away_score,
        "score_diff": home_score - away_score,
        "home_win_probability": game.get("home_win_probability"),
    }

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


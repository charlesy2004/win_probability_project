import redis
import os
import json
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
LIVE_GAMES_KEY = "nba:games:live"
GAME_LATEST_KEY_PREFIX = "nba:game"
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "120"))

if not REDIS_URL:
    raise ValueError("Failed to initialize Redis client")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)
def set_live_games(games: list[dict]) -> None:
    payload = {
        "games": games,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    redis_client.set(
        LIVE_GAMES_KEY, 
        json.dumps(payload), 
        ex=CACHE_TTL_SECONDS
    )

    for game in games:
        game_id = game.get("game_id")
        if not game_id:
            continue

        redis_client.set(
            f"{GAME_LATEST_KEY_PREFIX}:{game_id}:latest",
            json.dumps(
                {
                    "game": game,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            ),
            ex=CACHE_TTL_SECONDS,
        )
    
def get_live_games_from_cache() -> dict | None:
    cached = redis_client.get(LIVE_GAMES_KEY)

    if not cached:
        return None
    payload = json.loads(cached)
    return payload.get("games")

def get_game_from_cache(game_id: str) -> dict | None:
    cached = redis_client.get(f"{GAME_LATEST_KEY_PREFIX}:{game_id}:latest")

    if not cached:
        return None
    
    payload = json.loads(cached)
    return payload.get("game")
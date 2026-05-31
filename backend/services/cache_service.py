import json
import os
from datetime import datetime, timezone

import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
LIVE_GAMES_KEY = "nba:games:live"
GAME_LATEST_KEY_PREFIX = "nba:game"
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "120"))

redis_client = None

if REDIS_URL:
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
    except Exception:
        redis_client = None

def set_live_games(games: list[dict]) -> None:
    if redis_client is None:
        return

    updated_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "games": games,
        "updated_at": updated_at,
    }

    redis_client.set(
        LIVE_GAMES_KEY,
        json.dumps(payload),
        ex=CACHE_TTL_SECONDS,
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
                    "updated_at": updated_at,
                }
            ),
            ex=CACHE_TTL_SECONDS,
        )


def get_live_games_from_cache() -> list[dict] | None:
    if redis_client is None:
        return None

    cached = redis_client.get(LIVE_GAMES_KEY)

    if not cached:
        return None

    payload = json.loads(cached)
    return payload.get("games")


def get_game_from_cache(game_id: str) -> dict | None:
    if redis_client is None:
        return None

    cached = redis_client.get(f"{GAME_LATEST_KEY_PREFIX}:{game_id}:latest")

    if not cached:
        return None

    payload = json.loads(cached)
    return payload.get("game")


def set_game_plays(game_id: str, plays: list[dict]) -> None:
    if redis_client is None:
        return

    payload = {
        "plays": plays,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    redis_client.set(
        f"{GAME_LATEST_KEY_PREFIX}:{game_id}:plays",
        json.dumps(payload),
        ex=CACHE_TTL_SECONDS,
    )


def get_game_plays_from_cache(game_id: str) -> list[dict] | None:
    if redis_client is None:
        return None

    cached = redis_client.get(f"{GAME_LATEST_KEY_PREFIX}:{game_id}:plays")

    if not cached:
        return None

    payload = json.loads(cached)
    return payload.get("plays")
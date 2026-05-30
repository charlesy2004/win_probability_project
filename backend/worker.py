import os
import time
import logging
from dotenv import load_dotenv

from db.session import session_local
from services.espn_service import fetch_espn_scoreboard, format_game, ESPN_SCOREBOARD_URL
from services.snapshot_service import save_scoreboard_snapshots
from services.raw_payload_service import save_raw_espn_scoreboard_payload
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

SNAPSHOT_INTERVAL_SECONDS = int(os.getenv("SNAPSHOT_INTERVAL_SECONDS", "60"))


def capture_scoreboard_snapshot_once() -> int:
    db = session_local()

    try:
        raw_payload = fetch_espn_scoreboard()
        save_raw_espn_scoreboard_payload(db, raw_payload, endpoint=ESPN_SCOREBOARD_URL)
        events = raw_payload.get("events", [])
        logging.info(f"Fetched raw ESPN scoreboard payload with {len(events)} events")
        games = [format_game(event) for event in events]
        inserted_count = save_scoreboard_snapshots(db, games)
        db.commit()
        logging.info(
            "Snapshot complete: games=%s inserted=%s",
            len(games),
            inserted_count,
        )
        return inserted_count
        # games = get_live_games()
        # inserted_count = save_scoreboard_snapshots(db, games)

        # logging.info(
        #     "Snapshot complete: games=%s inserted=%s",
        #     len(games),
        #     inserted_count,
        # )

        # return inserted_count

    except Exception:
        db.rollback()
        logging.exception("Snapshot failed")
        return 0

    finally:
        db.close()


def main() -> None:
    logging.info(
        "Starting NBA snapshot worker. Interval=%s seconds",
        SNAPSHOT_INTERVAL_SECONDS,
    )

    try:
        while True:
            capture_scoreboard_snapshot_once()
            time.sleep(SNAPSHOT_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        logging.info("Snapshot worker stopped by user")


if __name__ == "__main__":
    main()
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from db.models import RawEspnScoreboardPayload
def save_raw_espn_scoreboard_payload(db: Session, payload: dict, endpoint: str) -> RawEspnScoreboardPayload | None:
    raw_payload = RawEspnScoreboardPayload(
        source="espn",
        endpoint=endpoint,
        payload=payload,
        event_cnt = len(payload.get("events", [])),
        created_at=datetime.now(timezone.utc)
    )
    db.add(raw_payload)
    return raw_payload
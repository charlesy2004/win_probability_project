from datetime import datetime, timezone
from sqlalchemy.orm import Session
from db.models import RawEspnScoreboardPayload
import json
import hashlib

def calculate_payload_hash(payload: dict) -> str:
    payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
def save_raw_espn_scoreboard_payload(db: Session, payload: dict, endpoint: str) -> tuple[RawEspnScoreboardPayload, bool]:
    payload_hash = calculate_payload_hash(payload)
    existing_payload = db.query(RawEspnScoreboardPayload).filter_by(payload_hash=payload_hash).first()
    if existing_payload:
        return existing_payload, False

    raw_payload = RawEspnScoreboardPayload(
        source="espn",
        endpoint=endpoint,
        payload=payload,
        payload_hash=payload_hash,
        event_cnt = len(payload.get("events", [])),
        created_at=datetime.now(timezone.utc)
    )
    db.add(raw_payload)
    return raw_payload, True
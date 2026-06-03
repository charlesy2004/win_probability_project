import json
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
RAW_PAYLOAD_BUCKET = os.getenv("RAW_PAYLOAD_BUCKET", "raw-espn-payloads")


if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is not set")

if not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY is not set")


supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def build_raw_payload_storage_path(payload_hash: str) -> str:
    now = datetime.now(timezone.utc)

    return (
        f"source=espn/"
        f"endpoint=scoreboard/"
        f"year={now.year}/"
        f"month={now.month:02d}/"
        f"day={now.day:02d}/"
        f"{payload_hash}.json"
    )


def upload_raw_payload_to_storage(
    payload: dict,
    payload_hash: str,
) -> tuple[str, str]:
    storage_path = build_raw_payload_storage_path(payload_hash)

    payload_bytes = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    supabase.storage.from_(RAW_PAYLOAD_BUCKET).upload(
        path=storage_path,
        file=payload_bytes,
        file_options={
            "content-type": "application/json",
            "upsert": "false",
        },
    )

    return RAW_PAYLOAD_BUCKET, storage_path
from sqlalchemy.orm import Session

from db.models import HistoricalGameState


def bulk_create_historical_game_states(
    db: Session,
    rows: list[dict],
) -> int:
    """
    Bulk insert historical game-state rows for one game.

    This is much faster than inserting/checking one play at a time.

    Duplicate prevention:
    - Query existing action_numbers for the game once
    - Insert only rows with new action_numbers
    """
    if not rows:
        return 0

    game_id = rows[0]["game_id"]

    existing_action_numbers = {
        action_number
        for (action_number,) in (
            db.query(HistoricalGameState.action_number)
            .filter(HistoricalGameState.game_id == game_id)
            .all()
        )
    }

    new_rows = [
        row
        for row in rows
        if row.get("action_number") is not None
        and row.get("action_number") not in existing_action_numbers
    ]

    if not new_rows:
        return 0

    db.bulk_insert_mappings(HistoricalGameState, new_rows)
    db.commit()

    return len(new_rows)
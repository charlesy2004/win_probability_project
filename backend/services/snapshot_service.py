from sqlalchemy.orm import Session
from db.models import ScoreboardSnapshot
from zoneinfo import ZoneInfo
from services.prediction_service import calculate_seconds_remaining, calculate_game_progress

def save_scoreboard_snapshot(db: Session, game: dict) -> ScoreboardSnapshot | None:
    home_score = game["home_score"]
    away_score = game["away_score"]
    period = game.get("period")
    clock = game.get("clock")

    score_diff = home_score - away_score
    seconds_remaining = calculate_seconds_remaining(period, clock)
    game_progress = calculate_game_progress(period, clock)
    existing_snapshot = (
        db.query(ScoreboardSnapshot)
        .filter(ScoreboardSnapshot.game_id == game["game_id"])
        .filter(ScoreboardSnapshot.seconds_remaining == seconds_remaining)
        .first()
    )
    snapshot = ScoreboardSnapshot(
        game_id=game["game_id"],
        name=game.get("name"),
        short_name=game.get("short_name"),
        home_team=game["home_team"],
        away_team=game["away_team"],
        home_team_abbr=game.get("home_team_abbr"),
        away_team_abbr=game.get("away_team_abbr"),
        home_score=home_score,
        away_score=away_score,
        score_diff=score_diff,
        seconds_remaining=seconds_remaining,
        game_progress=game_progress,
        period=period,
        clock=clock,
        status=game.get("status"),
        home_win_probability=game["home_win_probability"],
        model_type="xgboost",
        model_version="v1",
    )

    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    return snapshot


def save_scoreboard_snapshots(db: Session, games: list[dict]) -> int:
    inserted_count = 0

    for game in games:
        snapshot = save_scoreboard_snapshot(db, game)

        if snapshot is not None:
            inserted_count += 1

    return inserted_count


def get_snapshots_for_game(db: Session, game_id: str) -> list[dict]:
    eastern = ZoneInfo("America/New_York")

    snapshots = (
        db.query(ScoreboardSnapshot)
        .filter(ScoreboardSnapshot.game_id == game_id)
        .order_by(ScoreboardSnapshot.created_at.asc())
        .all()
    )

    return [
        {
            "time": snapshot.created_at.astimezone(eastern).strftime("%I:%M:%S %p"),
            "home_win_probability": snapshot.home_win_probability,
            "home_score": snapshot.home_score,
            "away_score": snapshot.away_score,
            "period": snapshot.period,
            "clock": snapshot.clock,
            "status": snapshot.status,
        }
        for snapshot in snapshots
    ]
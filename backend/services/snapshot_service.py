from sqlalchemy.orm import Session

from db.models import ScoreboardSnapshot


def save_scoreboard_snapshot(db: Session, game: dict) -> ScoreboardSnapshot:
    snapshot = ScoreboardSnapshot(
        game_id=game["game_id"],
        name=game.get("name"),
        short_name=game.get("short_name"),

        home_team=game["home_team"],
        away_team=game["away_team"],
        home_team_abbr=game.get("home_team_abbr"),
        away_team_abbr=game.get("away_team_abbr"),

        home_score=game["home_score"],
        away_score=game["away_score"],

        period=game.get("period"),
        clock=game.get("clock"),
        status=game.get("status"),

        home_win_probability=game["home_win_probability"],
    )

    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    return snapshot


def save_scoreboard_snapshots(db: Session, games: list[dict]) -> int:
    for game in games:
        save_scoreboard_snapshot(db, game)

    return len(games)

def get_snapshots_for_game(db: Session, game_id: str) -> list[dict]:
    snapshots = (
        db.query(ScoreboardSnapshot)
        .filter(ScoreboardSnapshot.game_id == game_id)
        .order_by(ScoreboardSnapshot.created_at.asc())
        .all()
    )

    return [
        {
            "time": snapshot.created_at.isoformat(),
            "home_win_probability": snapshot.home_win_probability,
            "home_score": snapshot.home_score,
            "away_score": snapshot.away_score,
            "period": snapshot.period,
            "clock": snapshot.clock,
        }
        for snapshot in snapshots
    ]
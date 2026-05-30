from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, Float, DateTime, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ScoreboardSnapshot(Base):
    __tablename__ = "scoreboard_snapshots"

    __table_args__ = (
        UniqueConstraint(
            "game_id",
            "seconds_remaining",
            name="uq_scoreboard_snapshot_game_time_left",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    game_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=True)
    short_name = Column(String, nullable=True)

    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    home_team_abbr = Column(String, nullable=True)
    away_team_abbr = Column(String, nullable=True)

    home_score = Column(Integer, nullable=False)
    away_score = Column(Integer, nullable=False)
    score_diff = Column(Integer, nullable=True)
    seconds_remaining = Column(Integer, nullable=True)
    game_progress = Column(Float, nullable=True)
    period = Column(Integer, nullable=True)
    clock = Column(String, nullable=True)
    status = Column(String, nullable=True)

    home_win_probability = Column(Float, nullable=False)

    model_type = Column(String, nullable=False)
    model_version = Column(String, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

class HistoricalGameState(Base):
    __tablename__ = "historical_game_states"

    id = Column(Integer, primary_key=True, index=True)

    game_id = Column(String, index=True, nullable=False)

    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)

    home_score = Column(Integer, nullable=False)
    away_score = Column(Integer, nullable=False)
    score_diff = Column(Integer, nullable=False)

    period = Column(Integer, nullable=False)
    clock = Column(String, nullable=False)
    seconds_remaining = Column(Integer, nullable=False)
    game_progress = Column(Float, nullable=False)

    home_win_probability_baseline = Column(Float, nullable=True)

    final_home_score = Column(Integer, nullable=True)
    final_away_score = Column(Integer, nullable=True)
    home_team_won = Column(Integer, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
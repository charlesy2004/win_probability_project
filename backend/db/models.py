from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ScoreboardSnapshot(Base):
    __tablename__ = "scoreboard_snapshots"

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

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
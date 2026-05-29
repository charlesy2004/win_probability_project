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

class HistoricalGameState(Base):
    __tablename__ = "historical_game_states"

    id = Column(Integer, primary_key=True, index=True)

    game_id = Column(String, index=True, nullable=False)
    season = Column(String, nullable=True)
    season_type = Column(String, nullable=True)

    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    home_team_abbr = Column(String, nullable=True)
    away_team_abbr = Column(String, nullable=True)

    home_score = Column(Integer, nullable=False)
    away_score = Column(Integer, nullable=False)
    score_diff = Column(Integer, nullable=False)

    period = Column(Integer, nullable=False)
    clock = Column(String, nullable=False)
    raw_clock = Column(String, nullable=True)

    seconds_remaining = Column(Integer, nullable=False)
    game_progress = Column(Float, nullable=False)

    action_number = Column(Integer, nullable=True)
    action_type = Column(String, nullable=True)
    sub_type = Column(String, nullable=True)
    description = Column(String, nullable=True)

    team_tricode = Column(String, nullable=True)
    player_name = Column(String, nullable=True)

    shot_value = Column(Integer, nullable=True)
    shot_result = Column(String, nullable=True)
    is_field_goal = Column(Integer, nullable=True)
    shot_distance = Column(Float, nullable=True)

    home_win_probability_baseline = Column(Float, nullable=True)

    final_home_score = Column(Integer, nullable=True)
    final_away_score = Column(Integer, nullable=True)
    home_team_won = Column(Integer, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
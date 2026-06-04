from __future__ import annotations


def get_latest_play_with_possession(plays: list[dict]) -> dict | None:
    for play in plays:
        if play.get("possession_team_id"):
            return play

    return None


def resolve_possession_team(
    plays: list[dict],
    home_team_id: str | None,
    away_team_id: str | None,
    home_team_name: str,
    away_team_name: str,
) -> str | None:
    latest_play = get_latest_play_with_possession(plays)

    if latest_play is None:
        return None

    possession_team_id = str(latest_play.get("possession_team_id"))

    if home_team_id and possession_team_id == str(home_team_id):
        return home_team_name

    if away_team_id and possession_team_id == str(away_team_id):
        return away_team_name

    return None


def is_foul_play(play: dict) -> bool:
    play_type = str(play.get("type") or "").lower()
    text = str(play.get("text") or "").lower()

    return "foul" in play_type or "foul" in text


def calculate_current_period_team_fouls(
    plays: list[dict],
    period: int,
    home_team_id: str | None,
    away_team_id: str | None,
) -> tuple[int | None, int | None]:
    if not period:
        return None, None

    home_fouls = 0
    away_fouls = 0

    for play in plays:
        if int(play.get("period") or 0) != int(period):
            continue

        if not is_foul_play(play):
            continue

        team_id = play.get("team_id")

        if team_id is None:
            continue

        if home_team_id and str(team_id) == str(home_team_id):
            home_fouls += 1

        elif away_team_id and str(team_id) == str(away_team_id):
            away_fouls += 1

    return home_fouls, away_fouls


def is_in_bonus(team_fouls: int | None) -> bool:
    if team_fouls is None:
        return False

    # NBA bonus starts after the 4th team foul in a quarter.
    # This is an approximation from ESPN play-by-play.
    return team_fouls >= 5


def build_live_game_context(
    plays: list[dict],
    period: int,
    home_team_id: str | None,
    away_team_id: str | None,
    home_team_name: str,
    away_team_name: str,
) -> dict:
    possession_team = resolve_possession_team(
        plays=plays,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        home_team_name=home_team_name,
        away_team_name=away_team_name,
    )

    home_fouls, away_fouls = calculate_current_period_team_fouls(
        plays=plays,
        period=period,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
    )

    return {
        "possession_team": possession_team,
        "home_fouls": home_fouls,
        "away_fouls": away_fouls,
        "home_in_bonus": is_in_bonus(home_fouls),
        "away_in_bonus": is_in_bonus(away_fouls),
    }
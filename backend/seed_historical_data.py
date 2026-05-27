import random

from db.session import session_local
from services.historical_data_service import create_historical_game_state


def generate_synthetic_historical_rows(num_games: int = 200):
    db = session_local()

    try:
        for game_num in range(num_games):
            game_id = f"synthetic_{game_num}"

            final_home_score = random.randint(90, 130)
            final_away_score = random.randint(90, 130)

            # Create several fake game states per game
            for period in [1, 2, 3, 4]:
                for clock in ["12:00", "06:00", "02:00"]:
                    # Earlier states are noisier; later states closer to final score
                    progress_factor = {
                        1: 0.25,
                        2: 0.50,
                        3: 0.75,
                        4: 0.90,
                    }[period]

                    home_score = int(final_home_score * progress_factor) + random.randint(-6, 6)
                    away_score = int(final_away_score * progress_factor) + random.randint(-6, 6)

                    home_score = max(home_score, 0)
                    away_score = max(away_score, 0)

                    create_historical_game_state(
                        db=db,
                        game_id=game_id,
                        home_team="Synthetic Home",
                        away_team="Synthetic Away",
                        home_score=home_score,
                        away_score=away_score,
                        period=period,
                        clock=clock,
                        final_home_score=final_home_score,
                        final_away_score=final_away_score,
                    )

        print(f"Inserted synthetic historical rows for {num_games} games.")

    finally:
        db.close()


if __name__ == "__main__":
    generate_synthetic_historical_rows()
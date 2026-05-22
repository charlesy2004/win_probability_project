import { useEffect, useState } from "react";
import "./App.css";

type Game = {
  game_id: string;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  period: number;
  clock: string;
  home_win_probability: number;
};

function App() {
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("https://humble-pancake-jjv7j7rq76j735v56-8000.app.github.dev/games/live")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to fetch games");
        }
        return response.json();
      })
      .then((data) => {
        setGames(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <h1>Loading games...</h1>;
  }

  if (error) {
    return <h1>Error: {error}</h1>;
  }

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">NBA Live Model</p>
        <h1>Win Probability Dashboard</h1>
        
        <p className="subtitle">
          Live game state, score, and model-estimated home team win probability.
        </p>
      </section>

      <section className="games-grid">
        {games.map((game) => (
          <article className="game-card" key={game.game_id}>
            <div className="game-header">
              <div>
                <p className="matchup">
                  {game.away_team} @ {game.home_team}
                </p>
                <p className="game-status">
                  Q{game.period} · {game.clock}
                </p>
              </div>

              <span className="badge">
                {(game.home_win_probability * 100).toFixed(0)}%
              </span>
            </div>

            <div className="score-row">
              <div>
                <p className="team-name">{game.away_team}</p>
                <p className="score">{game.away_score}</p>
              </div>

              <div>
                <p className="team-name">{game.home_team}</p>
                <p className="score">{game.home_score}</p>
              </div>
            </div>

            <div className="probability-section">
              <div className="probability-label">
                <span>{game.home_team} win probability</span>
                <span>
                  {(game.home_win_probability * 100).toFixed(1)}%
                </span>
              </div>

              <div className="probability-bar">
                <div
                  className="probability-fill"
                  style={{
                    width: `${game.home_win_probability * 100}%`,
                  }}
                />
              </div>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}

export default App;
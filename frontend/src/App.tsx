import { useEffect, useState } from "react";
import "./App.css";

type Game = {
  game_id: string;
  name: string;
  short_name: string;
  date: string;

  home_team: string;
  home_team_abbr: string;
  home_score: number;
  home_record: string;

  away_team: string;
  away_team_abbr: string;
  away_score: number;
  away_record: string;

  period: number;
  clock: string;
  status: string;
  detail: string;

  venue: string;
  series: string;
  broadcast: string;

  spread: string;
  over_under: number | null;

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
                  {game.away_team_abbr} @ {game.home_team_abbr}
                </p>
                <p className="game-status">
                  {game.detail || game.status}
                </p>
                <p className="game-status">
                  {game.series}
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
            <div className="game-meta">
              <p>Venue: {game.venue}</p>
              <p>Broadcast: {game.broadcast || "TBD"}</p>
              <p>
                Odds: {game.spread || "N/A"}
                {game.over_under !== null ? ` | O/U ${game.over_under}` : ""}
              </p>
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
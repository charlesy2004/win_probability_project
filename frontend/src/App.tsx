import { useEffect, useState } from "react";
import "./App.css";
import GameCard from "./components/GameCard";

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
          <GameCard key={game.game_id} game={game} />
        ))}
      </section>
    </main>
  );
}

export default App;
import { useEffect, useState } from "react";
import "./App.css";
import GameCard from "./components/GameCard";
import WinProbabilityChart from "./components/WinProbabilityChart";
import type { Game, TimelinePoint } from "./types/game";
import { fetchLiveGames, fetchWinProbabilityTimeline, saveScoreboardSnapshots } from "./api/clients";

function App() {
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const gamesData = await fetchLiveGames();
        setGames(gamesData);

        if (gamesData.length > 0) {
          const timelineData = await fetchWinProbabilityTimeline(
            gamesData[0].game_id
          );
          setTimeline(timelineData);
        }

        setLoading(false);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("Something went wrong");
        }

        setLoading(false);
      }
    }

    loadDashboardData();
  }, []);
  async function handleSaveSnapshot() {
  try {
    await saveScoreboardSnapshots();

    if (games.length > 0) {
      const timelineData = await fetchWinProbabilityTimeline(games[0].game_id);
      setTimeline(timelineData);
    }
  } catch (err) {
    if (err instanceof Error) {
      setError(err.message);
    } else {
      setError("Something went wrong");
    }
  }
}
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
        <button className="save-button" onClick={handleSaveSnapshot}>
          Save Snapshot
        </button>
      </section>

      <section className="games-grid">
        {games.map((game) => (
          <GameCard key={game.game_id} game={game} />
        ))}
      </section>

      {timeline.length > 0 && <WinProbabilityChart timeline={timeline} />}
    </main>
  );
}

export default App;
import { useEffect, useState } from "react";
import "./App.css";
import GameCard from "./components/GameCard";
import WinProbabilityChart from "./components/WinProbabilityChart";
import PlayByPlayCard from "./components/PlayByPlayCard";
import GameStateCard from "./components/GameStateCard";
import type { Game, TimelinePoint, LivePlay, GameStateDashboard } from "./types/game";
import {
  fetchLiveGames,
  fetchWinProbabilityTimeline,
  fetchGamePlays,
  fetchGameState,
} from "./api/clients";

function App() {
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [plays, setPlays] = useState<LivePlay[]>([]);
  const [gameState, setGameState] = useState<GameStateDashboard | null>(null);
  useEffect(() => {
    async function loadDashboardData() {
      try {
        const gamesData = await fetchLiveGames();
        setGames(gamesData);

        if (gamesData.length > 0) {
          const gameId = gamesData[0].game_id;

          const timelineData = await fetchWinProbabilityTimeline(gameId);
          setTimeline(timelineData);

          const playsData = await fetchGamePlays(gameId);
          setPlays(playsData);

          const stateData = await fetchGameState(gameId);
          setGameState(stateData);
        }
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("Something went wrong");
        }
      } finally {
        setLoading(false);
      }
    }

    loadDashboardData();

    const intervalId = setInterval(() => {
      loadDashboardData();
    }, 30000);

    return () => {
      clearInterval(intervalId);
    };
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
          Live game state and neural-network-estimated home team win probability.
        </p>

        <p className="model-badge">Neural Network v1</p>
      </section>

      <section className="games-grid">
        {games.map((game) => (
          <GameCard
            key={game.game_id}
            game={game}
            state={gameState?.game_id === game.game_id ? gameState : null}
          />
        ))}
      </section>

      {timeline.length > 0 && <WinProbabilityChart timeline={timeline} />}

      {<GameStateCard state={gameState} />}

      <PlayByPlayCard plays={plays} />
    </main>
  );
}

export default App;
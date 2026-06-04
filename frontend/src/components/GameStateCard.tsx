import type { GameStateDashboard } from "../types/game";

type GameStateCardProps = {
  state: GameStateDashboard | null;
};

function formatScoreDiff(scoreDiff: number) {
  if (scoreDiff > 0) {
    return `Home +${scoreDiff}`;
  }

  if (scoreDiff < 0) {
    return `Away +${Math.abs(scoreDiff)}`;
  }

  return "Tied";
}

function formatModelSource(modelSource?: string | null): string {
  if (modelSource === "neural_network_v1") {
    return "Neural Network v1";
  }

  if (modelSource?.includes("fallback")) {
    return "Fallback model";
  }

  return "Unavailable";
}

function FoulsDisplay({
  label,
  fouls,
  inBonus,
}: {
  label?: string | null;
  fouls?: number | null;
  inBonus?: boolean | null;
}) {
  return (
    <div className="state-metric">
      <p className="state-label">{label ?? "--"} Fouls</p>

      <p className={inBonus ? "state-value bonus" : "state-value"}>
        {fouls ?? "--"}
        {inBonus && <span className="bonus-tag"> BONUS</span>}
      </p>
    </div>
  );
}

function GameStateCard({ state }: GameStateCardProps) {
  if (!state) {
    return null;
  }

  const hasWinProbability =
    typeof state.home_win_probability === "number" &&
    !Number.isNaN(state.home_win_probability);

  const winPercent = hasWinProbability
    ? `${(state.home_win_probability * 100).toFixed(1)}%`
    : "Unavailable";

  const matchupAway = state.away_team_abbr ?? state.away_team ?? "--";
  const matchupHome = state.home_team_abbr ?? state.home_team ?? "--";
  const homeLabel = state.home_team_abbr ?? state.home_team ?? "Home";
  const awayLabel = state.away_team_abbr ?? state.away_team ?? "Away";

  return (
    <section className="state-card">
      <div className="state-card-header">
        <h2>Game State Dashboard</h2>

        <p>
          {matchupAway} @ {matchupHome}
        </p>

        <p className="game-status">
          Model: {formatModelSource(state.model_source)}
        </p>
      </div>

      <div className="state-grid">
        <div className="state-metric">
          <p className="state-label">Game Clock</p>
          <p className="state-value">
            {state.period && state.period > 0
              ? `Q${state.period} ${state.clock ?? "--"}`
              : "Not Started"}
          </p>
        </div>

        <div className="state-metric">
          <p className="state-label">Score Differential</p>
          <p className="state-value">{formatScoreDiff(state.score_diff)}</p>
        </div>

        <div className="state-metric">
          <p className="state-label">Possession</p>
          <p className="state-value">{state.possession_team ?? "--"}</p>
        </div>

        <div className="state-metric">
          <p className="state-label">{homeLabel} Win %</p>
          <p className="state-value">{winPercent}</p>
        </div>

        <FoulsDisplay
          label={homeLabel}
          fouls={state.home_fouls}
          inBonus={state.home_in_bonus}
        />

        <FoulsDisplay
          label={awayLabel}
          fouls={state.away_fouls}
          inBonus={state.away_in_bonus}
        />
      </div>
    </section>
  );
}

export default GameStateCard;
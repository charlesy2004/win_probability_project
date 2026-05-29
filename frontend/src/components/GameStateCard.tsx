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

function FoulsDisplay({
  label,
  fouls,
  inBonus,
}: {
  label: string;
  fouls: number | null;
  inBonus: boolean;
}) {
  return (
    <div className="state-metric">
      <p className="state-label">{label} Fouls</p>

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

  const winPercent = `${(state.home_win_probability * 100).toFixed(1)}%`;

  return (
    <section className="state-card">
      <div className="state-card-header">
        <h2>Game State Dashboard</h2>
        <p>
          {state.away_team_abbr} @ {state.home_team_abbr}
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
          <p className="state-label">{state.home_team_abbr} Win %</p>
          <p className="state-value">{winPercent}</p>
        </div>

        <FoulsDisplay
          label={state.home_team_abbr}
          fouls={state.home_fouls}
          inBonus={state.home_in_bonus}
        />

        <FoulsDisplay
          label={state.away_team_abbr}
          fouls={state.away_fouls}
          inBonus={state.away_in_bonus}
        />
      </div>
    </section>
  );
}

export default GameStateCard;
import type { Game, GameStateDashboard } from "../types/game";

type GameCardProps = {
  game: Game;
  state?: GameStateDashboard | null;
};

function formatModelSource(modelSource?: string | null): string {
  if (modelSource === "neural_network_v1") {
    return "Neural Network v1";
  }

  if (modelSource?.includes("fallback")) {
    return "Fallback model";
  }

  return "Unavailable";
}

function GameCard({ game, state }: GameCardProps) {
  const homeWinProbability =
    state?.home_win_probability ?? game.home_win_probability;

  const modelSource = state?.model_source ?? game.model_source;

  const hasWinProbability =
    typeof homeWinProbability === "number" &&
    !Number.isNaN(homeWinProbability);

  const winProbabilityPercent = hasWinProbability
    ? homeWinProbability * 100
    : null;

  const period = state?.period ?? game.period;
  const clock = state?.clock ?? game.clock;
  const status = state?.status ?? game.detail ?? game.status;

  const homeScore = state?.home_score ?? game.home_score;
  const awayScore = state?.away_score ?? game.away_score;

  return (
    <article className="game-card">
      <div className="game-header">
        <div>
          <p className="matchup">
            {game.away_team_abbr} @ {game.home_team_abbr}
          </p>

          <p className="game-status">
            {clock && period ? `${clock} - ${period > 4 ? "OT" : `${period}${period === 1 ? "st" : period === 2 ? "nd" : period === 3 ? "rd" : "th"} Quarter`}` : status}
          </p>

          <p className="game-status">
            Model: {formatModelSource(modelSource)}
          </p>

          {game.series && <p className="game-status">{game.series}</p>}
        </div>

        <span className="badge">
          {winProbabilityPercent !== null
            ? `${winProbabilityPercent.toFixed(0)}%`
            : "N/A"}
        </span>
      </div>

      <div className="score-row">
        <div>
          <p className="team-name">{game.away_team}</p>
          <p className="score">{awayScore}</p>
        </div>

        <div>
          <p className="team-name">{game.home_team}</p>
          <p className="score">{homeScore}</p>
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
            {winProbabilityPercent !== null
              ? `${winProbabilityPercent.toFixed(1)}%`
              : "Unavailable"}
          </span>
        </div>

        <div className="probability-bar">
          <div
            className="probability-fill"
            style={{
              width:
                winProbabilityPercent !== null
                  ? `${winProbabilityPercent}%`
                  : "0%",
            }}
          />
        </div>
      </div>
    </article>
  );
}

export default GameCard;
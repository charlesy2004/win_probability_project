import type { Game } from "../types/game";

type GameCardProps = {
  game: Game;
};

function GameCard({ game }: GameCardProps) {
  return (
    <article className="game-card">
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
  );
}

export default GameCard;
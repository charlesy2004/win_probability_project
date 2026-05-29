import type { LivePlay } from "../types/game";

type PlayByPlayCardProps = {
  plays: LivePlay[];
};

function PlayByPlayCard({ plays }: PlayByPlayCardProps) {
  return (
    <section className="play-card">
      <div className="play-card-header">
        <h2>Live Play-by-Play</h2>
        <p>{plays.length} events</p>
      </div>

      {plays.length === 0 ? (
        <p className="empty-state">
          No play-by-play available yet. This usually means the game has not
          started.
        </p>
      ) : (
        <div className="play-list">
          {plays.map((play, index) => {
            const winProbability =
              play.home_win_probability !== null
                ? `${(play.home_win_probability * 100).toFixed(1)}%`
                : "--";

            return (
              <article key={play.id ?? index} className="play-row">
                <div className="play-time">
                  Q{play.period ?? "-"} {play.clock ?? ""}
                </div>

                <div className="play-main">
                  <p className="play-description">
                    {play.text ?? "No description available"}
                  </p>

                  <p className="play-meta">
                    {play.team && <span>{play.team}</span>}
                    {play.type && <span>{play.type}</span>}
                  </p>
                </div>

                <div className="play-score">
                  <p>
                    {play.away_score ?? "-"} - {play.home_score ?? "-"}
                  </p>
                  <p className="play-wp">WP: {winProbability}</p>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

export default PlayByPlayCard;
import type { LivePlay } from "../types/game";

type PlayByPlayCardProps = {
  plays: LivePlay[];
};

function PlayByPlayCard({ plays }: PlayByPlayCardProps) {
  const latestPlays = [...plays]
    .sort(
      (a, b) =>
        Number(b.sequence_number ?? 0) - Number(a.sequence_number ?? 0)
    )
    .slice(0, 25);

  return (
    <section className="play-card">
      <div className="play-card-header">
        <h2>Live Play-by-Play</h2>
        <p>
          Latest {latestPlays.length} of {plays.length} events
        </p>
      </div>

      {latestPlays.length === 0 ? (
        <p className="empty-state">
          No play-by-play available yet. This usually means the game has not
          started.
        </p>
      ) : (
        <div className="play-list">
          {latestPlays.map((play, index) => {
            const homeWinProbability = play.home_win_probability;

            const hasWinProbability =
              typeof homeWinProbability === "number" &&
              !Number.isNaN(homeWinProbability);

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

                  {hasWinProbability && (
                    <p className="play-wp">
                      WP: {(homeWinProbability * 100).toFixed(1)}%
                    </p>
                  )}
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
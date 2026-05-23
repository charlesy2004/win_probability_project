import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

import type { TimelinePoint } from "../types/game";

type WinProbabilityChartProps = {
  timeline: TimelinePoint[];
};

function WinProbabilityChart({ timeline }: WinProbabilityChartProps) {
  const chartData = timeline.map((point, index) => ({
    event_index: index + 1,
    time: point.time,
    probability_percent: point.home_win_probability * 100,
  }));

  return (
    <section className="chart-card">
      <h2>Win Probability Timeline</h2>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis domain={[0, 100]} tickFormatter={(value) => `${value}%`} />
          <Tooltip
            formatter={(value) => [
              `${Number(value).toFixed(1)}%`,
              "Home Win Probability",
            ]}
            labelFormatter={(label) => `Game Time: ${label}`}
          />
          <Line
            type="monotone"
            dataKey="probability_percent"
            strokeWidth={3}
            dot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </section>
  );
}

export default WinProbabilityChart;
import { useEffect, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { getProphetForecastData } from "../services/api";

export default function ProphetChart({ componentId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchChart() {
      try {
        setLoading(true);
        const res = await getProphetForecastData(componentId);
        setData(res);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchChart();
  }, [componentId]);

  if (loading) {
    return (
      <div className="ir-chart-loading">
        <span className="spinner" />
        <p>Generating Prophet Time Series...</p>
      </div>
    );
  }

  if (error || !data || data.status === "error") {
    const errorDetails = error || data?.message || "Could not load forecast";
    const displayMsg = typeof errorDetails === "object" ? JSON.stringify(errorDetails) : errorDetails;
    return (
      <div className="ir-chart-error">
        <p>⚠️ {displayMsg}</p>
      </div>
    );
  }

  const chartData = data.timeseries || [];
  const reorderLevel = data.reorder_level || 0;

  return (
    <div className="ir-chart-container">
      <h4 className="ir-chart-title">Prophet 90-Day Forecast Trend</h4>
      <div style={{ width: "100%", height: 300 }}>
        <ResponsiveContainer>
          <AreaChart
            data={chartData}
            margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id="colorStock" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--accent-light)" stopOpacity={0.4} />
                <stop offset="95%" stopColor="var(--accent-light)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis
              dataKey="date"
              stroke="var(--text-muted)"
              tick={{ fontSize: 12 }}
              tickFormatter={(v) => {
                const d = new Date(v);
                return `${d.getMonth() + 1}/${d.getDate()}`;
              }}
            />
            <YAxis stroke="var(--text-muted)" tick={{ fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--bg-card)",
                borderColor: "var(--glass-border)",
                borderRadius: "8px",
                color: "var(--text-primary)",
              }}
              itemStyle={{ color: "var(--text-primary)" }}
            />
            {reorderLevel > 0 && (
              <ReferenceLine
                y={reorderLevel}
                stroke="var(--warning)"
                strokeDasharray="4 4"
                label={{
                  position: "insideTopLeft",
                  value: "Reorder",
                  fill: "var(--warning)",
                  fontSize: 12,
                }}
              />
            )}
            <ReferenceLine
              y={0}
              stroke="var(--error)"
              strokeDasharray="4 4"
              label={{
                position: "insideBottomLeft",
                value: "Stockout",
                fill: "var(--error)",
                fontSize: 12,
              }}
            />
            <Area
              type="monotone"
              dataKey="predicted_stock"
              stroke="var(--accent-light)"
              strokeWidth={3}
              fillOpacity={1}
              fill="url(#colorStock)"
              name="Predicted Stock"
              activeDot={{ r: 6, fill: "var(--accent-light)", stroke: "#fff" }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

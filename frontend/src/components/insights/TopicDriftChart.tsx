import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { TopicDrift } from "../../types";

const TOPIC_COLORS: Record<string, string> = {
  exploration: "#E8A33D",
  reserves: "#C0392B",
  "seam-quality": "#5E9EDB",
  environment: "#46A758",
  production: "#6D6A5C",
  compliance: "#8B5CF6",
};

export function TopicDriftChart({ data }: { data: TopicDrift[] }) {
  // Transform: [{quarter, topics:[{key,weight,...}]}] → [{quarter, key1: weight1, ...}]
  const transformed = data.map((d) => {
    const row: Record<string, string | number> = { quarter: d.quarter };
    for (const t of d.topics) {
      row[t.key] = t.weight;
    }
    return row;
  });

  // Collect all topic keys present in data
  const topicKeys = [...new Set(data.flatMap((d) => d.topics.map((t) => t.key)))];

  if (data.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-[13px] text-ink/40">
        No topic data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={transformed} margin={{ top: 6, right: 6, bottom: 0, left: -10 }}>
        <defs>
          {topicKeys.map((key) => (
            <linearGradient key={key} id={`grad-${key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={TOPIC_COLORS[key] ?? "#999"} stopOpacity={0.35} />
              <stop offset="95%" stopColor={TOPIC_COLORS[key] ?? "#999"} stopOpacity={0.02} />
            </linearGradient>
          ))}
        </defs>
        <XAxis
          dataKey="quarter"
          tick={{ fontSize: 10.5, fill: "#8b8d94" }}
          tickLine={false}
          axisLine={{ stroke: "#e5e6eb" }}
        />
        <YAxis
          tick={{ fontSize: 10.5, fill: "#8b8d94" }}
          tickLine={false}
          axisLine={false}
          domain={[0, 1]}
        />
        <Tooltip
          contentStyle={{
            fontSize: 12,
            borderRadius: 8,
            border: "1px solid #e5e6eb",
            boxShadow: "0 2px 12px rgba(11,27,43,0.10)",
            fontFamily: "Inter Variable, Inter, sans-serif",
          }}
          formatter={(value: number, name: string) => [value.toFixed(2), name.replace("-", " ").replace(/\b\w/g, l => l.toUpperCase())]}
        />
        {topicKeys.map((key) => (
          <Area
            key={key}
            type="monotone"
            dataKey={key}
            stackId="1"
            stroke={TOPIC_COLORS[key] ?? "#999"}
            fill={`url(#grad-${key})`}
            strokeWidth={1.5}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}
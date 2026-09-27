import { useEffect, useState } from "react";
import {
  Clock,
  Target,
  Cpu,
  MessageSquareText,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { api } from "../../lib/api";
import { PageHeader } from "../../components/shared/PageHeader";
import { StatRowSkeleton } from "../../components/shared/LoadingSkeleton";
import { StatCard } from "../../components/shared/StatCard";
import type { MetricSummary, MetricPoint } from "../../types";

export function Metrics() {
  const [summary, setSummary] = useState<MetricSummary | null>(null);
  const [trends, setTrends] = useState<MetricPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.metrics.summary(), api.metrics.trends()])
      .then(([s, t]) => { setSummary(s); setTrends(t); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-7">
      <PageHeader
        title="Impact Metrics"
        description="CoalMitra's measurable reduction in manual report preparation time."
        eyebrow="Metrics"
      />

      {loading ? (
        <StatRowSkeleton count={4} />
      ) : summary ? (
        <>
          {/* Primary stat cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Report prep time reduction"
              value={`${Math.round(summary.report_prep_reduction_pct)}%`}
              hint="vs manual baseline"
              icon={<Clock className="h-5 w-5" />}
              tone="gold"
              trend="up"
            />
            <StatCard
              label="Extraction accuracy"
              value={`${Math.round(summary.extraction_accuracy_pct)}%`}
              hint="mean field confidence"
              icon={<Target className="h-5 w-5" />}
              tone="green"
              trend="up"
            />
            <StatCard
              label="Automation rate"
              value={`${Math.round(summary.automation_pct)}%`}
              hint="READY without manual review"
              icon={<Cpu className="h-5 w-5" />}
              tone="blue"
              trend="up"
            />
            <StatCard
              label="Query resolution rate"
              value={`${Math.round(summary.query_resolution_pct)}%`}
              hint="answers with citation"
              icon={<MessageSquareText className="h-5 w-5" />}
              tone="default"
              trend="up"
            />
          </div>

          {/* Sparkline charts */}
          {trends.length > 0 && (
            <div className="grid gap-5 sm:grid-cols-2">
              <SparklineCard
                title="Report preparation time (min)"
                data={trends}
                dataKey="report_prep_min"
                color="#E8A33D"
                downward
              />
              <SparklineCard
                title="Extraction accuracy (%)"
                data={trends}
                dataKey="extraction_accuracy_pct"
                color="#46A758"
              />
              <SparklineCard
                title="Automation rate (%)"
                data={trends}
                dataKey="automation_pct"
                color="#5E9EDB"
              />
              <SparklineCard
                title="Query resolution (%)"
                data={trends}
                dataKey="query_resolution_pct"
                color="#8B5CF6"
              />
            </div>
          )}

          {/* Secondary stats */}
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard
              label="Docs processed"
              value={`${summary.docs_processed}/${summary.docs_total}`}
              tone="default"
            />
            <StatCard
              label="Open anomalies"
              value={String(summary.anomalies_open)}
              tone={summary.anomalies_open > 0 ? "red" : "green"}
            />
            <StatCard
              label="Avg response time"
              value={`${Math.round(summary.avg_response_ms)}ms`}
              tone="default"
            />
            <StatCard
              label="Overall trend"
              value={summary.trend === "up" ? "▲" : summary.trend === "down" ? "▼" : "◆"}
              hint={summary.trend === "up" ? "Improving" : summary.trend === "down" ? "Declining" : "Stable"}
              tone={summary.trend === "up" ? "green" : summary.trend === "down" ? "red" : "default"}
            />
          </div>
        </>
      ) : (
        <p className="py-12 text-center text-[14px] text-ink/50">
          No metrics available. Run the seed to populate data.
        </p>
      )}
    </div>
  );
}

function SparklineCard({
  title,
  data,
  dataKey,
  color,
  downward,
}: {
  title: string;
  data: MetricPoint[];
  dataKey: string;
  color: string;
  downward?: boolean;
}) {
  const values = data.map((d) => (d as any)[dataKey] as number).filter(Boolean);
  const first = values[0] ?? 0;
  const last = values[values.length - 1] ?? 0;
  const change = first ? ((last - first) / first) * 100 : 0;
  const improving = downward ? change < 0 : change > 0;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex items-start justify-between">
        <p className="text-[12.5px] font-medium text-ink/60">{title}</p>
        <span
          className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10.5px] font-semibold ${
            improving
              ? "bg-success/10 text-success"
              : "bg-danger/10 text-danger"
          }`}
        >
          {change > 0 ? "+" : ""}{change.toFixed(1)}%
        </span>
      </div>
      <div className="mt-3 h-16">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis dataKey="captured_on" hide />
            <YAxis hide domain={["auto", "auto"]} />
            <Tooltip
              contentStyle={{
                fontSize: 11,
                borderRadius: 6,
                border: "1px solid #e5e6eb",
                fontFamily: "Inter Variable, Inter, sans-serif",
              }}
              formatter={(value: number) => [value.toFixed(1), title.split("(")[0].trim()]}
              labelFormatter={(label: string) => {
                const d = new Date(label);
                return d.toLocaleDateString("en-IN", { month: "short", year: "numeric" });
              }}
            />
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 2, fill: "white" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
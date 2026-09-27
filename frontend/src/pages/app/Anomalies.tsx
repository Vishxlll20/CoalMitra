import { useEffect, useState } from "react";
import { CheckCircle2, Eye } from "lucide-react";
import { api } from "../../lib/api";
import { severityClass } from "../../lib/format";
import { PageHeader } from "../../components/shared/PageHeader";
import { EmptyState } from "../../components/shared/EmptyState";
import { StatRowSkeleton } from "../../components/shared/LoadingSkeleton";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { SourcePill } from "../../components/shared/SourcePill";
import { StatCard } from "../../components/shared/StatCard";
import type { Anomaly } from "../../types";
import { toast } from "sonner";
import { useRoleStore } from "../../stores/role";

export function Anomalies() {
  const role = useRoleStore((state) => state.role);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.anomalies
      .all()
      .then(setAnomalies)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const openCount = anomalies.filter((a) => a.status === "open").length;
  const highCount = anomalies.filter((a) => a.severity === "HIGH" || a.severity === "CRITICAL").length;

  const handleAck = async (id: string) => {
    try {
      const acked = await api.anomalies.acknowledge(id);
      setAnomalies((prev) => prev.map((a) => (a.id === id ? acked : a)));
      toast.success("Anomaly acknowledged");
    } catch {
      toast.error("Failed to acknowledge");
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Anomalies"
        description="Deviations from coalfield historical baselines, flagged by severity."
        eyebrow="Anomalies"
      />

      {!loading && anomalies.length > 0 && (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard label="Open" value={String(openCount)} tone={openCount > 0 ? "red" : "green"} />
          <StatCard label="High/Critical" value={String(highCount)} tone={highCount > 0 ? "red" : "green"} />
          <StatCard label="Field" value={String(new Set(anomalies.map((a) => a.field_key)).size)} />
          <StatCard label="Coalfields" value={String(new Set(anomalies.map((a) => a.block)).size)} />
        </div>
      )}

      {loading ? (
        <StatRowSkeleton count={2} />
      ) : anomalies.length === 0 ? (
        <EmptyState
          icon={<CheckCircle2 className="h-6 w-6 text-success" />}
          title="No anomalies detected"
          copy="All field values fall within expected ranges for their coalfield baselines."
        />
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
          <table className="w-full text-left text-[13px]">
            <thead>
              <tr className="border-b border-slate-200 bg-paper-warm text-[10.5px] font-semibold uppercase tracking-[0.1em] text-ink/45">
                <th className="px-5 py-3">Severity</th>
                <th className="px-5 py-3">Field</th>
                <th className="px-5 py-3">Block</th>
                <th className="px-5 py-3">Expected</th>
                <th className="px-5 py-3">Actual</th>
                <th className="px-5 py-3">Deviation</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {anomalies.map((a) => (
                <tr key={a.id} className="border-b border-slate-50 last:border-0 hover:bg-paper-warm/30">
                  <td className="px-5 py-3">
                    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10.5px] font-bold ${severityClass(a.severity)}`}>
                      {a.severity}
                    </span>
                  </td>
                  <td className="px-5 py-3 font-medium text-navy-900">
                    {a.field_label}
                  </td>
                  <td className="px-5 py-3 text-ink/60">{a.block}</td>
                  <td className="px-5 py-3 text-ink/50">
                    {a.baseline_doc_id ? (
                      <SourcePill
                        refData={{
                          document_id: a.baseline_doc_id,
                          display: a.expected_value,
                          page: a.baseline_page_number,
                          bbox: a.baseline_bbox,
                          confidence: a.baseline_confidence,
                          value: a.expected_value,
                        }}
                        origin="anomaly"
                        label={a.expected_value}
                      />
                    ) : a.expected_value}
                  </td>
                  <td className="px-5 py-3 font-semibold text-navy-800">
                    <SourcePill
                      refData={{
                        document_id: a.primary_doc_id,
                        display: a.actual_value,
                        page: 1,
                        bbox: { x0: 0.1, y0: 0.2, x1: 0.3, y1: 0.25 },
                        confidence: 0.85,
                        value: a.actual_value,
                      }}
                      origin="anomaly"
                      label={a.actual_value}
                    />
                  </td>
                  <td className="px-5 py-3">
                    <span className={`font-semibold ${a.deviation_pct > 15 ? "text-danger" : a.deviation_pct > 5 ? "text-gold-600" : "text-ink/60"}`}>
                      {a.deviation_pct > 0 ? "+" : ""}{a.deviation_pct.toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <Badge tone={a.status === "open" ? "red" : "green"}>
                      {a.status}
                    </Badge>
                  </td>
                  <td className="px-5 py-3">
                    {a.status === "open" && role === "AUDITOR" && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleAck(a.id)}
                      >
                        <Eye className="h-3 w-3" /> Ack
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
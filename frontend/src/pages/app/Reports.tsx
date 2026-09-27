import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  FileText,
  RefreshCw,
} from "lucide-react";
import { api } from "../../lib/api";
import { fmtDate } from "../../lib/format";
import { PageHeader } from "../../components/shared/PageHeader";
import { EmptyState } from "../../components/shared/EmptyState";
import { StatRowSkeleton } from "../../components/shared/LoadingSkeleton";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import type { Report } from "../../types";
import { toast } from "sonner";

export function Reports() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    api.reports
      .list()
      .then(setReports)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const report = await api.reports.generate();
      setReports((prev) => [report, ...prev]);
      toast.success("Report generated");
    } catch {
      toast.error("Failed to generate report");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reports"
        description="Auto-generated, fully traceable analysis reports."
        eyebrow="Reports"
        actions={
          <Button variant="gold" onClick={handleGenerate} disabled={generating}>
            <RefreshCw className={`h-3.5 w-3.5 ${generating ? "animate-spin" : ""}`} />
            {generating ? "Generating…" : "Generate new report"}
          </Button>
        }
      />

      {loading ? (
        <StatRowSkeleton count={2} />
      ) : reports.length === 0 ? (
        <EmptyState
          icon={<FileText className="h-6 w-6" />}
          title="No reports yet"
          copy="Reports are auto-generated from ingested documents. You can also generate one manually."
          action={
            <Button variant="gold" onClick={handleGenerate} disabled={generating} className="mt-2">
              Generate first report
            </Button>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {reports.map((r) => (
            <Link
              key={r.id}
              to={`/app/reports/${r.id}`}
              className="group rounded-xl border border-slate-200 bg-white p-5 transition-all hover:border-gold-500/40 hover:shadow-glow"
            >
              <div className="flex items-start justify-between">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-navy-900/5 text-navy-700 transition-colors group-hover:bg-gold-100 group-hover:text-gold-600">
                  <FileText className="h-5 w-5" />
                </div>
                <Badge tone={r.status === "ready" ? "green" : "neut"}>
                  {r.status}
                </Badge>
              </div>
              <h3 className="mt-3 font-display text-[14.5px] font-semibold text-navy-900 leading-snug group-hover:text-gold-600 transition-colors">
                {r.title}
              </h3>
              <p className="mt-1.5 line-clamp-2 text-[12px] text-ink/50">{r.summary}</p>
              <div className="mt-3 flex items-center gap-3 text-[11px] text-ink/40">
                <span>{fmtDate(r.generated_at)}</span>
                <span>·</span>
                <span>{r.total_refs ?? 0} traceable refs</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
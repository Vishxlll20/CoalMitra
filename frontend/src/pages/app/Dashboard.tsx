import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  FolderOpen,
  FileText,
  AlertTriangle,
  MessageSquareText,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
} from "lucide-react";
import { useRoleStore } from "../../stores/role";
import { api } from "../../lib/api";
import { PageHeader } from "../../components/shared/PageHeader";
import { StatCard } from "../../components/shared/StatCard";
import { StatRowSkeleton } from "../../components/shared/LoadingSkeleton";
import type { DashboardPayload } from "../../types";

const K = (s: DashboardPayload["stats"], k: string) => Number(s[k] ?? 0);

export function Dashboard() {
  const roleMeta = useRoleStore((s) => s.roleMeta);
  const role = useRoleStore((s) => s.role);
  const [dash, setDash] = useState<DashboardPayload | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.dashboard
      .role(role)
      .then(setDash)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [role]);

  const stats = dash?.stats ?? {};
  const highlights = dash?.highlights ?? [];
  const anomaliesOpen = K(stats, "anomalies_open");
  const queriesAnswered = K(stats, "queries_answered");

  return (
    <div className="space-y-7">
      <PageHeader
        title={`Good morning, ${roleMeta.label}`}
        description={roleMeta.blurb}
        eyebrow={roleMeta.label}
      />

      {loading ? (
        <StatRowSkeleton count={4} />
      ) : (
        <>
          {/* Stat cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Documents"
              value={String(stats.documents ?? 0)}
              hint={`${stats.documents_total ?? 0} total in corpus`}
              icon={<FolderOpen className="h-5 w-5" />}
              tone="gold"
            />
            <StatCard
              label="Reports"
              value={String(stats.reports ?? 0)}
              hint={`${stats.reports_recent ?? 0} generated this month`}
              icon={<FileText className="h-5 w-5" />}
              tone="default"
            />
            <StatCard
              label="Open anomalies"
              value={String(anomaliesOpen)}
              hint="requiring review"
              icon={<AlertTriangle className="h-5 w-5" />}
              tone={anomaliesOpen > 0 ? "red" : "green"}
              trend={anomaliesOpen > 0 ? "up" : undefined}
            />
            <StatCard
              label="AI queries"
              value={String(queriesAnswered)}
              hint={`${stats.resolution_rate ?? "—"}% resolution rate`}
              icon={<MessageSquareText className="h-5 w-5" />}
              tone="blue"
            />
          </div>

          {/* Highlights strip */}
          {highlights.length > 0 && (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {highlights.map((h, i) => {
                const ICON_MAP: Record<string, typeof TrendingUp> = {
                  FileText: FileText,
                  AlertTriangle: AlertTriangle,
                  MessageSquare: MessageSquareText,
                  CheckCircle: CheckCircle2,
                  FileSearch: FolderOpen,
                  Database: FolderOpen,
                  Target: TrendingUp,
                  Shield: CheckCircle2,
                  check: CheckCircle2,
                  alert: AlertCircle,
                };
                const IconComp = ICON_MAP[h.icon] ?? TrendingUp;
                return (
                  <div
                    key={i}
                    className={`flex items-center gap-3 rounded-lg border px-4 py-3 text-[12.5px] font-medium ${
                      h.tone === "success" || h.tone === "green"
                        ? "border-success/20 bg-success/5 text-success"
                        : h.tone === "warning" || h.tone === "amber"
                          ? "border-gold-500/30 bg-gold-100/50 text-gold-600"
                          : h.tone === "danger" || h.tone === "red"
                            ? "border-danger/20 bg-danger/5 text-danger"
                            : "border-slate-200 bg-white text-ink/70"
                    }`}
                  >
                    <IconComp className="h-4 w-4 shrink-0" />
                    <div className="min-w-0">
                      <p className="truncate font-semibold">{h.label}</p>
                      <p className="truncate text-[11px] opacity-70">{h.value}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Quick links */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {(role === "MINISTRY_OFFICIAL" ? [
              { to: "/app/reports", label: "View reports", icon: FileText, sub: "Ready-to-use official summaries" },
              { to: "/app/query", label: "Ask a question", icon: MessageSquareText, sub: "Get a cited answer in English or Hindi" },
              { to: "/app/metrics", label: "View metrics", icon: TrendingUp, sub: "Track processing and resolution" },
            ] : role === "AUDITOR" ? [
              { to: "/app/documents", label: "Browse source records", icon: FolderOpen, sub: "Inspect extracted evidence" },
              { to: "/app/reports", label: "Review reports", icon: FileText, sub: "Follow figures to their sources" },
              { to: "/app/anomalies", label: "Review anomalies", icon: AlertTriangle, sub: "Resolve flagged deviations" },
            ] : [
              { to: "/app/documents", label: "Browse documents", icon: FolderOpen, sub: "Ingested PDFs and scans" },
              { to: "/app/reports", label: "View reports", icon: FileText, sub: "Auto-generated summaries" },
              { to: "/app/anomalies", label: "Review anomalies", icon: AlertTriangle, sub: "Deviations flagged this quarter" },
            ]).map(({ to, label, icon: Icon, sub }) => (
              <Link
                key={to}
                to={to}
                className="group flex items-center gap-4 rounded-lg border border-slate-200 bg-white p-5 transition-all hover:border-gold-500/40 hover:shadow-glow"
              >
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-paper-warm text-navy-700 transition-colors group-hover:bg-gold-100 group-hover:text-gold-600">
                  <Icon className="h-5 w-5" />
                </div>
                <div className="min-w-0">
                  <p className="text-[13.5px] font-semibold text-navy-900">{label}</p>
                  <p className="text-[11.5px] text-ink/50">{sub}</p>
                </div>
                <ArrowRight className="ml-auto h-4 w-4 text-ink/20 transition-colors group-hover:text-gold-600" />
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
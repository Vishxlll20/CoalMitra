import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  Download,
} from "lucide-react";
import { api } from "../../lib/api";
import { fmtDate } from "../../lib/format";
import { PageHeader } from "../../components/shared/PageHeader";
import { CardSkeleton } from "../../components/shared/LoadingSkeleton";
import { Badge } from "../../components/ui/Badge";
import { SourcePill } from "../../components/shared/SourcePill";
import type { Report, ReportSection } from "../../types";

function numericValue(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value !== "string") return null;
  const match = value.replace(/,/g, "").match(/-?\d+(?:\.\d+)?/);
  return match ? Number(match[0]) : null;
}

function matchingTableRef(section: ReportSection, cell: unknown, column: number) {
  if (column !== 1) return undefined;
  const display = String(cell).trim().replace(/\s+/g, " ");
  const cellNumber = numericValue(cell);
  return section.refs?.find((ref) => {
    if (ref.page <= 0) return false;
    if (cellNumber !== null && typeof ref.value === "number") {
      return Math.abs(cellNumber - ref.value) < 1e-7;
    }
    return String(ref.display).trim().replace(/\s+/g, " ") === display;
  });
}

export function ReportDetail() {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    api.reports
      .get(id)
      .then(setReport)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <CardSkeleton rows={8} />;
  if (!report)
    return (
      <div className="text-center py-20 text-ink/50 text-[14px]">
        Report not found.{" "}
        <Link to="/app/reports" className="text-gold-600 underline">Back to reports</Link>
      </div>
    );

  return (
    <div className="space-y-6 max-w-4xl">
      <Link
        to="/app/reports"
        className="inline-flex items-center gap-1.5 text-[12px] font-medium text-ink/45 transition-colors hover:text-ink/70"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to reports
      </Link>

      <PageHeader
        title={report.title}
        description={report.summary}
        eyebrow="Report"
        actions={
          <a
            href={api.reports.exportUrl(report.id)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-md bg-navy-900 px-3.5 py-1.5 text-[12.5px] font-medium text-paper transition-colors hover:bg-navy-800"
          >
            <Download className="h-3.5 w-3.5" /> Export PDF
          </a>
        }
      />

      {/* Report metadata */}
      <div className="flex items-center gap-3 text-[12px] text-ink/50">
        <Badge tone="neut">{report.role.replace("_", " ")}</Badge>
        <span>·</span>
        <span>{fmtDate(report.generated_at)}</span>
        <span>·</span>
        <span>{report.total_refs ?? 0} traceable values</span>
      </div>

      {/* Sections — narrative with inline SourcePills */}
      {report.sections?.map((section, si) => (
        <section key={si} className="rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="mb-3 font-display text-[16px] font-semibold text-navy-900">
            {section.title}
          </h2>
          <SectionContent section={section} />
        </section>
      ))}
    </div>
  );
}

/**
 * Renders a section's narrative content, replacing any refs with
 * clickable SourcePills. Narrative is stored as paragraphs or table data.
 */
function SectionContent({ section }: { section: ReportSection }) {
  // If it's a table section, render as a table
  if (section.kind === "table") {
    const rows = (section.content as any)?.rows ?? [];
    const headers = (section.content as any)?.headers ?? [];
    return (
      <table className="w-full text-left text-[13px]">
        <thead>
          <tr className="border-b border-slate-200 text-[10.5px] font-semibold uppercase tracking-[0.1em] text-ink/45">
            {headers.map((h: string, i: number) => (
              <th key={i} className="pb-2 pr-4">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row: any[], ri: number) => (
            <tr key={ri} className="border-b border-slate-50 last:border-0">
              {row.map((cell: any, ci: number) => {
                const ref = matchingTableRef(section, cell, ci);
                return (
                  <td key={ci} className="py-2.5 pr-4">
                    {ref ? (
                      <SourcePill
                        refData={ref}
                        origin="report"
                        label={String(cell)}
                      />
                    ) : (
                      <span>{String(cell)}</span>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  // Narrative: render paragraphs with inline ref substitution
  const paragraphs = (section.content as any)?.paragraphs ?? [section.content as unknown as string];
  const refs = section.refs ?? [];

  return (
    <div className="space-y-3 prose-coal text-[14px] leading-relaxed">
      {paragraphs.map((para: string, pi: number) => {
        // Find any refs that appear in this paragraph by display text
        let parts: React.ReactNode[] = [para];
        for (const ref of refs) {
          const display = String(ref.display);
          parts = parts.flatMap<React.ReactNode>((part) => {
            if (typeof part !== "string") return [part];
            const idx = part.indexOf(display);
            if (idx === -1) return [part];
            const before = part.slice(0, idx);
            const after = part.slice(idx + display.length);
            return [
              before,
              <SourcePill key={`${pi}-${ref.value}-${ref.page}`} refData={ref} origin="report" label={display} />,
              after,
            ];
          });
        }
        return <p key={pi}>{parts}</p>;
      })}
    </div>
  );
}
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  FileText,
  Layers,
  Calendar,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { api } from "../../lib/api";
import { fmtDate, fmtBytes, confidenceTone } from "../../lib/format";
import { PageHeader } from "../../components/shared/PageHeader";
import { StatCard } from "../../components/shared/StatCard";
import { StatRowSkeleton, CardSkeleton } from "../../components/shared/LoadingSkeleton";
import { SourcePill } from "../../components/shared/SourcePill";
import type { Document, FieldExtraction, PageResult } from "../../types";
import { useRoleStore } from "../../stores/role";
import { toast } from "sonner";

export function DocumentDetail() {
  const { id } = useParams<{ id: string }>();
  const role = useRoleStore((state) => state.role);
  const [doc, setDoc] = useState<Document | null>(null);
  const [fields, setFields] = useState<FieldExtraction[]>([]);
  const [pages, setPages] = useState<PageResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [showRaw, setShowRaw] = useState(false);
  const [editingFieldId, setEditingFieldId] = useState<string | null>(null);
  const [correctedValue, setCorrectedValue] = useState("");
  const [savingCorrection, setSavingCorrection] = useState(false);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    Promise.all([api.documents.get(id), api.documents.fields(id), api.documents.pages(id)])
      .then(([d, f, p]) => {
        setDoc(d);
        setFields(f);
        setPages(p);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="space-y-6">
        <StatRowSkeleton count={4} />
        <CardSkeleton rows={6} />
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="text-center py-20 text-ink/50 text-[14px]">
        Document not found.{" "}
        <Link to="/app/documents" className="text-gold-600 underline">
          Back to documents
        </Link>
      </div>
    );
  }

  const tone = confidenceTone(doc.total_confidence);
  const avgConf = Math.round(doc.total_confidence * 100);

  const saveCorrection = async (field: FieldExtraction) => {
    if (!id) return;
    setSavingCorrection(true);
    try {
      const updated = await api.documents.correctField(id, field.id, correctedValue);
      setFields((current) => current.map((item) => item.id === updated.id ? updated : item));
      setEditingFieldId(null);
      toast.success("Correction saved and added to the audit trail");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not save correction");
    } finally {
      setSavingCorrection(false);
    }
  };

  return (
    <div className="space-y-6">
      <Link
        to="/app/documents"
        className="inline-flex items-center gap-1.5 text-[12px] font-medium text-ink/45 transition-colors hover:text-ink/70"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to documents
      </Link>

      <PageHeader
        title={doc.title}
        description={`${doc.block} · ${doc.district} · ${doc.category.replace("_", " ")}`}
        eyebrow="Document detail"
        actions={
          <a
            href={api.documents.fileUrl(doc.id)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-md border hairline bg-white px-3.5 py-1.5 text-[12.5px] font-medium text-ink/60 transition-colors hover:text-navy-900"
          >
            <FileText className="h-3.5 w-3.5" /> Open PDF
          </a>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          label="Confidence"
          value={`${avgConf}%`}
          tone={tone === "high" ? "green" : tone === "mid" ? "blue" : "red"}
        />
        <StatCard
          label="Pages"
          value={String(doc.page_count)}
          icon={<Layers className="h-5 w-5" />}
        />
        <StatCard
          label="Report date"
          value={fmtDate(doc.report_date)}
          icon={<Calendar className="h-5 w-5" />}
        />
        <StatCard
          label="File size"
          value={fmtBytes(doc.size_bytes)}
          icon={<FileText className="h-5 w-5" />}
        />
      </div>

      {/* Fields table */}
      <div className="rounded-xl border border-slate-200 bg-white">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3.5">
          <h2 className="font-display text-[15px] font-semibold text-navy-900">
            Extracted fields
            <span className="ml-2 text-[12px] font-normal text-ink/40">
              ({fields.length} found)
            </span>
          </h2>
          <button
            onClick={() => setShowRaw((v) => !v)}
            className="inline-flex items-center gap-1.5 text-[11.5px] font-medium text-ink/45 transition-colors hover:text-ink/70"
          >
            {showRaw ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            {showRaw ? "Hide raw text" : "Show raw text"}
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-[13px]">
            <thead>
              <tr className="border-b border-slate-100 bg-paper-warm text-[10.5px] font-semibold uppercase tracking-[0.1em] text-ink/45">
                <th className="px-5 py-2.5">Field</th>
                <th className="px-5 py-2.5">Value</th>
                <th className="px-5 py-2.5">Confidence</th>
                <th className="px-5 py-2.5">Page</th>
                <th className="px-5 py-2.5">Matched text</th>
              </tr>
            </thead>
            <tbody>
              {fields.map((f) => {
                const fTone = confidenceTone(f.confidence);
                return (
                  <tr key={f.id} className="border-b border-slate-50 last:border-0 hover:bg-paper-warm/30">
                    <td className="px-5 py-3">
                      <span className="font-medium text-navy-900">{f.field_label}</span>
                    </td>
                    <td className="px-5 py-3 font-semibold text-navy-800">
                      {editingFieldId === f.id ? (
                        <div className="flex min-w-56 items-center gap-2">
                          <input
                            aria-label={`Correct ${f.field_label}`}
                            value={correctedValue}
                            onChange={(event) => setCorrectedValue(event.target.value)}
                            className="h-8 min-w-0 flex-1 rounded border border-slate-300 px-2 text-[12px] font-normal outline-none focus:border-gold-600"
                          />
                          <button type="button" disabled={savingCorrection} onClick={() => void saveCorrection(f)} className="text-[11px] font-semibold text-success disabled:opacity-50">Save</button>
                          <button type="button" disabled={savingCorrection} onClick={() => setEditingFieldId(null)} className="text-[11px] font-medium text-ink/45">Cancel</button>
                        </div>
                      ) : (
                        <>
                          <SourcePill
                            refData={{
                              document_id: doc.id,
                              document_title: doc.title,
                              display: f.value,
                              page: f.page_number,
                              bbox: f.bbox,
                              confidence: f.confidence,
                              value: f.numeric_value ?? f.value,
                            }}
                            origin="field"
                            label={f.value}
                          />
                          {f.unit && (
                        <span className="ml-1 text-[12px] font-normal text-ink/40">{f.unit}</span>
                          )}
                          {role === "GEOLOGIST" && f.confidence < 0.98 && (
                            <button type="button" onClick={() => { setEditingFieldId(f.id); setCorrectedValue(f.value); }} className="ml-2 text-[10.5px] font-medium text-gold-700 underline underline-offset-2">Correct</button>
                          )}
                        </>
                      )}
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                          fTone === "high"
                            ? "bg-success/10 text-success"
                            : fTone === "mid"
                              ? "bg-info/10 text-info"
                              : "bg-danger/10 text-danger"
                        }`}
                      >
                        {Math.round(f.confidence * 100)}%
                      </span>
                    </td>
                    <td className="px-5 py-3 text-[12px] text-ink/50">p.{f.page_number}</td>
                    <td className="max-w-[260px] truncate px-5 py-3 text-[11.5px] text-ink/45 font-mono">
                      {f.matched_text}
                    </td>
                  </tr>
                );
              })}
              {fields.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-5 py-10 text-center text-[13px] text-ink/40">
                    No fields extracted for this document.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Page previews */}
      {pages.length > 0 && (
        <div>
          <h2 className="mb-3 font-display text-[15px] font-semibold text-navy-900">
            Page previews
          </h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {pages.map((p) => (
              <div
                key={p.page_number}
                className="group relative overflow-hidden rounded-lg border border-slate-200 bg-white"
              >
                <img
                  src={`/static/pages/${doc.id}/${p.page_number}.png`}
                  alt={`Page ${p.page_number}`}
                  className="w-full transition-transform duration-300 group-hover:scale-105"
                  loading="lazy"
                />
                <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-white/90 to-transparent px-3 py-2">
                  <span className="text-[11px] font-semibold text-navy-900">
                    Page {p.page_number}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Raw text toggle */}
      {showRaw && (
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h3 className="mb-2 text-[12px] font-semibold uppercase tracking-[0.1em] text-ink/40">
            Raw page text
          </h3>
          {pages.map((p) => (
            <div key={p.page_number} className="mb-3">
              <p className="mb-1 text-[11px] font-semibold text-navy-800">Page {p.page_number}</p>
              <pre className="whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-[11px] leading-relaxed text-ink/60 font-mono max-h-48 overflow-y-auto">
                {p.text}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
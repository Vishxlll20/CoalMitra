import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ExternalLink, FileText } from "lucide-react";
import { useTraceStore } from "../../stores/traceability";
import { PageCanvas } from "./PageCanvas";
import { api } from "../../lib/api";
import type { Document } from "../../types";

/**
 * Shared slide-in panel for traceability.
 * Lives in AppShell — renders on every /app/* route.
 * Accepts focus from SourcePill (report field, extraction chip, chat citation,
 * anomaly flag, export data point) and shows the source PDF page with
 * the exact region highlighted.
 */
export function SourcePanelHost() {
  const focus = useTraceStore((s) => s.focus);
  const dismiss = useTraceStore((s) => s.dismiss);
  const [doc, setDoc] = useState<Document | null>(null);
  const [ready, setReady] = useState(false);

  // Fetch document metadata whenever focus changes
  useEffect(() => {
    if (!focus?.ref.document_id) {
      setDoc(null);
      return;
    }
    let alive = true;
    setReady(false);
    api.documents
      .get(focus.ref.document_id)
      .then((d) => alive && setDoc(d))
      .catch(() => alive && setDoc(null))
      .finally(() => alive && setReady(true));
    return () => { alive = false; };
  }, [focus?.ref.document_id]);

  return (
    <AnimatePresence>
      {focus?.open && (
        <>
          {/* Backdrop */}
          <motion.div
            key="trace-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 bg-navy-950/20 backdrop-blur-[2px]"
            onClick={dismiss}
          />

          {/* Panel */}
          <motion.aside
            key="trace-panel"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 z-50 flex h-full w-[440px] max-w-[92vw] flex-col border-l border-slate-200 bg-white shadow-lift"
          >
            {/* Header */}
            <div className="flex items-center justify-between gap-3 border-b border-slate-200 px-5 py-4">
              <div className="flex items-center gap-3 min-w-0">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gold-100 text-gold-600">
                  <FileText className="h-4 w-4" />
                </div>
                <div className="min-w-0">
                  <p className="truncate text-[13px] font-semibold text-navy-900">
                    {focus.ref.display}
                  </p>
                  <p className="truncate text-[11.5px] text-ink/45">
                    Page {focus.ref.page} · {doc?.block ?? focus.ref.document_id}
                  </p>
                </div>
              </div>
              <button
                onClick={dismiss}
                className="flex h-8 w-8 items-center justify-center rounded-md text-ink/40 transition-colors hover:bg-slate-100 hover:text-ink"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Page preview with bbox */}
            <div className="flex-1 overflow-y-auto px-5 py-4">
              {ready ? (
                <>
                  <PageCanvas
                    documentId={focus.ref.document_id}
                    pageNumber={focus.ref.page}
                    bbox={focus.ref.bbox}
                  />

                  {/* Confidence badge */}
                  <div className="mt-3 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <ConfidenceBadge confidence={focus.ref.confidence} />
                      <span className="text-[11px] text-ink/40">
                        {confidenceLabel(focus.ref.confidence)}
                      </span>
                    </div>
                    <span className="text-[11px] text-ink/35">
                      Click the highlighted region to inspect raw text
                    </span>
                  </div>

                  {/* Document info */}
                  {doc && (
                    <div className="mt-4 rounded-lg border border-slate-200 bg-paper-warm p-3.5">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-ink/40">
                        Source document
                      </p>
                      <p className="mt-1 text-[13px] font-medium text-navy-900">{doc.title}</p>
                      <div className="mt-2 flex flex-wrap gap-2 text-[11.5px] text-ink/55">
                        <span>{doc.block}</span>
                        <span>·</span>
                        <span>{doc.district}</span>
                        <span>·</span>
                        <span>{doc.category.replace("_", " ")}</span>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="flex aspect-[595/842] items-center justify-center">
                  <div className="h-16 w-16 animate-pulse rounded-xl bg-slate-200" />
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center gap-3 border-t border-slate-200 px-5 py-3.5">
              <a
                href={api.documents.fileUrl(focus.ref.document_id)}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 rounded-md bg-navy-900 px-3.5 py-1.5 text-[12.5px] font-medium text-paper transition-colors hover:bg-navy-800 hover:shadow-md"
              >
                Open original PDF <ExternalLink className="h-3 w-3" />
              </a>
              <button
                onClick={dismiss}
                className="rounded-md border border-slate-200 bg-white px-3.5 py-1.5 text-[12.5px] font-medium text-ink/60 transition-colors hover:text-ink"
              >
                Close
              </button>
              <span className="ml-auto text-[10.5px] text-ink/30">
                {focus.origin === "report" && "Traced from report"}
                {focus.origin === "field" && "Traced from extraction"}
                {focus.origin === "chat" && "Traced from AI answer"}
                {focus.origin === "anomaly" && "Traced from anomaly"}
                {focus.origin === "export" && "Traced from export"}
              </span>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const tone =
    pct >= 85
      ? "bg-success/10 text-success border-success/20"
      : pct >= 65
        ? "bg-info/10 text-info border-info/20"
        : "bg-danger/10 text-danger border-danger/20";

  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11.5px] font-semibold ${tone}`}>
      {pct}% confidence
    </span>
  );
}

function confidenceLabel(c: number) {
  if (c >= 0.85) return "High confidence — rule + unit match";
  if (c >= 0.65) return "Moderate — phrase matched, unit inferred";
  return "Low — pattern-based estimate";
}
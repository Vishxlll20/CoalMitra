import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FolderOpen, Plus, FileText, ChevronRight } from "lucide-react";
import { api } from "../../lib/api";
import { fmtNum, fmtDate, fmtBytes, confidenceTone } from "../../lib/format";
import { PageHeader } from "../../components/shared/PageHeader";
import { EmptyState } from "../../components/shared/EmptyState";
import { StatRowSkeleton } from "../../components/shared/LoadingSkeleton";
import { Badge } from "../../components/ui/Badge";
import type { Document } from "../../types";
import { useDropzone } from "react-dropzone";
import { useRoleStore } from "../../stores/role";

export function Documents() {
  const role = useRoleStore((state) => state.role);
  const canUpload = role === "GEOLOGIST";
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    api.documents
      .list()
      .then(setDocs)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const { getRootProps, getInputProps, open } = useDropzone({
    noClick: true,
    disabled: !canUpload,
    accept: { "application/pdf": [".pdf"], "image/*": [".png", ".jpg", ".jpeg", ".tiff"] },
    onDrop: async (files) => {
      if (!files.length) return;
      setUploading(true);
      try {
        const uploaded = await api.documents.upload(files);
        setDocs((prev) => [...uploaded, ...prev]);
      } catch {
        /* toast handled by api.raw */
      } finally {
        setUploading(false);
      }
    },
  });

  return (
    <div
      {...getRootProps()}
      className={`space-y-6 ${uploading ? "ring-2 ring-gold-400/50 ring-offset-2 rounded-xl" : ""}`}
    >
      <input {...getInputProps()} />
      <PageHeader
        title="Documents"
        description="Uploaded geological reports, scans, and prospecting sheets."
        eyebrow="Documents"
        actions={canUpload ? (
          <button
            onClick={open}
            className="inline-flex items-center gap-2 rounded-md bg-gold-500 px-4 py-2 text-[12.5px] font-semibold text-navy-950 transition-colors hover:bg-gold-400"
          >
            <Plus className="h-3.5 w-3.5" /> Upload files
          </button>
        ) : undefined}
      />

      {loading ? (
        <StatRowSkeleton count={2} />
      ) : docs.length === 0 ? (
        <EmptyState
          icon={<FolderOpen className="h-6 w-6" />}
          title="No documents yet"
          copy="Upload PDFs, scanned geological reports, or prospecting sheets to begin."
          action={canUpload ? (
            <button
              onClick={open}
              className="mt-2 inline-flex items-center gap-2 rounded-md bg-gold-500 px-4 py-2 text-[12.5px] font-semibold text-navy-950 transition-colors hover:bg-gold-400"
            >
              <Plus className="h-3.5 w-3.5" /> Upload your first document
            </button>
          ) : undefined}
        />
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
          <table className="w-full text-left text-[13px]">
            <thead>
              <tr className="border-b border-slate-200 bg-paper-warm text-[11px] font-semibold uppercase tracking-[0.1em] text-ink/45">
                <th className="px-5 py-3">Document</th>
                <th className="px-5 py-3">Block</th>
                <th className="px-5 py-3">Category</th>
                <th className="px-5 py-3 text-right">Confidence</th>
                <th className="px-5 py-3 text-right">Date</th>
                <th className="w-10" />
              </tr>
            </thead>
            <tbody>
              {docs.map((doc) => {
                const tone = confidenceTone(doc.total_confidence);
                return (
                  <tr key={doc.id} className="group border-b border-slate-100 last:border-0 hover:bg-paper-warm/50">
                    <td className="px-5 py-3.5">
                      <Link
                        to={`/app/documents/${doc.id}`}
                        className="flex items-center gap-3"
                      >
                        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-navy-900/5 text-navy-700">
                          <FileText className="h-4 w-4" />
                        </div>
                        <div className="min-w-0">
                          <p className="truncate font-semibold text-navy-900 group-hover:text-gold-600 transition-colors">
                            {doc.title}
                          </p>
                          <p className="truncate text-[11.5px] text-ink/45">
                            {fmtBytes(doc.size_bytes)} · {fmtNum(doc.page_count)} pages
                          </p>
                        </div>
                      </Link>
                    </td>
                    <td className="px-5 py-3.5 text-[12.5px] text-ink/65">
                      {doc.block}
                    </td>
                    <td className="px-5 py-3.5">
                      <Badge tone="outline" className="text-[10.5px]">
                        {doc.category.replace("_", " ")}
                      </Badge>
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11.5px] font-semibold ${
                          tone === "high"
                            ? "bg-success/10 text-success"
                            : tone === "mid"
                              ? "bg-info/10 text-info"
                              : "bg-danger/10 text-danger"
                        }`}
                      >
                        {Math.round(doc.total_confidence * 100)}%
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-right text-[12px] text-ink/50">
                      {fmtDate(doc.report_date)}
                    </td>
                    <td className="px-2 py-3.5">
                      <ChevronRight className="h-4 w-4 text-ink/20 transition-colors group-hover:text-gold-600" />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {uploading && (
        <div className="fixed bottom-6 right-6 z-50 rounded-lg bg-navy-900 px-4 py-3 text-[12.5px] font-medium text-paper shadow-lift animate-rise">
          <span className="mr-2 inline-block h-3 w-3 animate-spin rounded-full border-2 border-gold-400 border-t-transparent" />
          Uploading files to pipeline…
        </div>
      )}
    </div>
  );
}
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronRight, X } from "lucide-react";
import { api } from "../../lib/api";
import { PageHeader } from "../../components/shared/PageHeader";
import { CardSkeleton } from "../../components/shared/LoadingSkeleton";
import { TopicDriftChart } from "../../components/insights/TopicDriftChart";
import { WordCloudViz } from "../../components/insights/WordCloudViz";
import { fmtDate } from "../../lib/format";
import type { WordStat, TopicDrift, Topic, TopicDocument } from "../../types";

export function Insights() {
  const [words, setWords] = useState<WordStat[]>([]);
  const [drift, setDrift] = useState<TopicDrift[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null);
  const [topicDocuments, setTopicDocuments] = useState<TopicDocument[]>([]);
  const [topicLoading, setTopicLoading] = useState(false);
  const [topicError, setTopicError] = useState("");

  useEffect(() => {
    Promise.all([api.insights.wordcloud(), api.insights.drift(), api.insights.topics()])
      .then(([w, d, t]) => { setWords(w); setDrift(d); setTopics(t); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function selectTopic(topic: Topic) {
    setSelectedTopic(topic);
    setTopicLoading(true);
    setTopicError("");
    try {
      setTopicDocuments(await api.insights.topicDocuments(topic.id));
    } catch (error) {
      setTopicDocuments([]);
      setTopicError(error instanceof Error ? error.message : "Could not load documents.");
    } finally {
      setTopicLoading(false);
    }
  }

  return (
    <div className="space-y-7">
      <PageHeader
        title="Insights"
        description="Topic drift, terminology patterns, and word clouds from the document corpus."
        eyebrow="Insights"
      />

      {loading ? (
        <div className="space-y-6">
          <CardSkeleton rows={3} />
          <CardSkeleton rows={4} />
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-5">
          {/* Word cloud — 2-col */}
          <div className="lg:col-span-2 rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="mb-4 font-display text-[14.5px] font-semibold text-navy-900">
              Word frequency
            </h2>
            <WordCloudViz words={words} />
          </div>

          {/* Topic drift — 3-col */}
          <div className="lg:col-span-3 rounded-xl border border-slate-200 bg-white p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display text-[14.5px] font-semibold text-navy-900">
                Topic drift over time
              </h2>
              <div className="flex items-center gap-1.5">
                {topics.map((t) => (
                  <button
                    type="button"
                    key={t.id}
                    aria-pressed={selectedTopic?.id === t.id}
                    onClick={() => void selectTopic(t)}
                    className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10.5px] font-semibold transition-shadow ${selectedTopic?.id === t.id ? "ring-2 ring-offset-1" : "hover:brightness-95"}`}
                    style={{ background: `${t.color}15`, color: t.color, ...(selectedTopic?.id === t.id ? { "--tw-ring-color": t.color } as React.CSSProperties : {}) }}
                  >
                    <span className="h-1.5 w-1.5 rounded-full" style={{ background: t.color }} />
                    {t.label}
                  </button>
                ))}
              </div>
            </div>
            <TopicDriftChart data={drift} />
          </div>
        </div>
      )}

      {selectedTopic && !loading && (
        <section className="border-t border-slate-200 pt-5" aria-live="polite">
          <div className="mb-3 flex items-center justify-between gap-3">
            <h2 className="font-display text-[15px] font-semibold text-navy-900">
              Documents in {selectedTopic.label}
            </h2>
            <button
              type="button"
              onClick={() => { setSelectedTopic(null); setTopicDocuments([]); setTopicError(""); }}
              className="inline-flex items-center gap-1.5 text-[12px] font-medium text-ink/55 hover:text-ink"
            >
              <X className="h-3.5 w-3.5" /> Clear filter
            </button>
          </div>
          {topicLoading ? (
            <p className="py-4 text-[13px] text-ink/50">Loading documents…</p>
          ) : topicError ? (
            <p role="alert" className="py-4 text-[13px] text-danger">{topicError}</p>
          ) : topicDocuments.length ? (
            <ul className="divide-y divide-slate-100 border-y border-slate-200">
              {topicDocuments.map((doc) => (
                <li key={doc.id}>
                  <Link to={`/app/documents/${doc.id}`} className="flex items-center gap-4 py-3 hover:bg-paper-warm/50">
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-[13px] font-medium text-navy-900">{doc.title}</span>
                      <span className="mt-0.5 block text-[11.5px] text-ink/50">{doc.block} · {doc.coalfield}</span>
                    </span>
                    <time className="shrink-0 text-[11.5px] text-ink/45">{fmtDate(doc.report_date)}</time>
                    <ChevronRight className="h-4 w-4 shrink-0 text-ink/30" />
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-4 text-[13px] text-ink/50">No documents are linked to this topic.</p>
          )}
        </section>
      )}
    </div>
  );
}
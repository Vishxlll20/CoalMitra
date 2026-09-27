import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowRight,
  FileText,
  Search,
  BarChart3,
  Mic,
  AlertTriangle,
  ShieldCheck,
} from "lucide-react";
import { api } from "../lib/api";
import type { Health, MetricSummary } from "../types";

const FEATURES = [
  {
    icon: FileText,
    title: "Structured Extraction",
    copy: "Scanned PDFs → field-level data with page, bbox, and confidence score — every number traceable.",
  },
  {
    icon: ShieldCheck,
    title: "Traceability Click-Through",
    copy: "Any report number clicks back to the exact line on the source PDF page, highlighted.",
  },
  {
    icon: BarChart3,
    title: "Topic & Word Insights",
    copy: "Term drift charts and word clouds show how coalfield language and concerns evolve over time.",
  },
  {
    icon: AlertTriangle,
    title: "Anomaly Detection",
    copy: "Deviations from coalfield baselines flagged by severity — reserves, GCV, overburden ratios.",
  },
  {
    icon: Search,
    title: "AI Query · हिंदी Support",
    copy: "RAG-grounded answers with inline citations in English and Hindi — or speak via mic.",
  },
  {
    icon: Mic,
    title: "Voice-First Input",
    copy: "Hindi voice queries via Whisper, optional TTS read-back. Works offline in demo mode.",
  },
];

export function Landing() {
  const [health, setHealth] = useState<Health | null>(null);
  const [metrics, setMetrics] = useState<MetricSummary | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() => {});
    api.metrics.summary().then(setMetrics).catch(() => {});
  }, []);

  const percent = (value: number | undefined) =>
    value === undefined ? "—" : `${Number(value.toFixed(1))}%`;
  const stats = [
    { value: percent(metrics?.report_prep_reduction_pct), label: "Report prep time reduction", sub: "vs manual baseline" },
    { value: percent(metrics?.extraction_accuracy_pct), label: "Extraction accuracy", sub: "mean field confidence" },
    { value: percent(metrics?.query_resolution_pct), label: "Query resolution rate", sub: "with citation grounding" },
    { value: health?.status === "ok" ? String(health.documents) : "—", label: "Seeded documents", sub: "across 7 coalfields" },
  ];

  return (
    <div className="min-h-screen bg-navy-950 text-white overflow-hidden">
      {/* Nav */}
      <nav className="relative z-10 mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gold-500 text-navy-950 font-display font-bold text-lg">
            C
          </div>
          <div>
            <span className="font-display text-[15.5px] font-semibold tracking-tight">CoalMitra</span>
            <span className="ml-2 text-[10.5px] uppercase tracking-[0.14em] text-gold-500/80">
              CMPDIL
            </span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {health?.status === "ok" && (
            <span className="hidden items-center gap-1.5 rounded-full border border-success/30 bg-success/10 px-2.5 py-1 text-[10.5px] font-semibold text-success md:flex">
              <span className="h-1.5 w-1.5 rounded-full bg-success" />
              Backend live · {health.documents} docs
            </span>
          )}
          <Link
            to="/app"
            className="inline-flex items-center gap-2 rounded-md bg-gold-500 px-4 py-2 text-[13px] font-semibold text-navy-950 transition-colors hover:bg-gold-400"
          >
            Open app <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative mx-auto max-w-6xl px-6 pt-20 pb-28">
        {/* Subtle grid background */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage:
              "linear-gradient(hsl(40 80% 60%) 1px, transparent 1px), linear-gradient(90deg, hsl(40 80% 60%) 1px, transparent 1px)",
            backgroundSize: "64px 64px",
          }}
        />

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="relative"
        >
          {/* Eyebrow */}
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-gold-500/30 bg-gold-500/10 px-3.5 py-1.5 text-[11.5px] font-semibold uppercase tracking-[0.14em] text-gold-400">
            <span className="h-1.5 w-1.5 rounded-full bg-gold-500" />
            Smart India Hackathon · Coal India Limited
          </div>

          <h1 className="font-display text-[clamp(36px,5vw,62px)] font-bold leading-[1.05] tracking-tight text-white max-w-3xl">
            Scattered coal reports.
            <br />
            <span className="text-gold-400">One intelligent answer.</span>
          </h1>

          <p className="mt-6 max-w-xl text-[16px] leading-relaxed text-slate-400">
            CoalMitra converts scanned geological documents from CMPDIL/CIL into
            auto-generated, fully traceable reports — with AI-powered queries in
            English and Hindi.
          </p>

          <div className="mt-8 flex items-center gap-4">
            <Link
              to="/app"
              className="inline-flex items-center gap-2 rounded-md bg-gold-500 px-5 py-2.5 text-[14px] font-semibold text-navy-950 transition-all hover:bg-gold-400 hover:shadow-[0_0_0_4px_rgba(232,163,61,0.25)]"
            >
              Enter dashboard <ArrowRight className="h-4 w-4" />
            </Link>
            <a
              href="#features"
              className="rounded-md border border-white/10 bg-white/5 px-5 py-2.5 text-[14px] font-medium text-slate-300 transition-colors hover:bg-white/10"
            >
              How it works
            </a>
          </div>
        </motion.div>

        {/* Decorative accent line */}
        <div className="absolute bottom-0 left-1/2 h-px w-48 -translate-x-1/2 bg-gradient-to-r from-transparent via-gold-500/40 to-transparent" />
      </section>

      {/* Stats strip */}
      <section className="border-y border-white/[0.06] bg-navy-900/60">
        <div className="mx-auto grid max-w-6xl grid-cols-2 gap-0 md:grid-cols-4">
          {stats.map((s, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: 0.1 + i * 0.06 }}
              className={`flex flex-col items-center px-6 py-6 ${i > 0 ? "border-l border-white/[0.06]" : ""}`}
            >
              <p className="font-display text-[28px] font-semibold text-gold-400">{s.value}</p>
              <p className="mt-0.5 text-[12.5px] font-semibold text-white">{s.label}</p>
              <p className="text-[11px] text-slate-500">{s.sub}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="mx-auto max-w-6xl px-6 py-20">
        <div className="mb-10 text-center">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-gold-500/80">
            Built for geological document intelligence
          </p>
          <h2 className="mt-2 font-display text-[28px] font-semibold text-white tracking-tight">
            From scanned pages to cited answers
          </h2>
        </div>

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, copy }, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: 0.08 + i * 0.05 }}
              className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-6 transition-colors hover:bg-white/[0.06] hover:border-white/[0.10]"
            >
              <div className="mb-3.5 flex h-10 w-10 items-center justify-center rounded-lg bg-gold-500/10 text-gold-500">
                <Icon className="h-5 w-5" />
              </div>
              <h3 className="font-display text-[15.5px] font-semibold text-white">{title}</h3>
              <p className="mt-1.5 text-[13px] leading-relaxed text-slate-400">{copy}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/[0.06]">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-gold-500 text-navy-950 font-display text-[11px] font-bold">
              C
            </div>
            <span className="text-[12px] font-semibold text-slate-400">
              CoalMitra · Central Mine Planning & Design Institute
            </span>
          </div>
          <p className="text-[11px] text-slate-600">
            Built for Smart India Hackathon · Hybrid demo pipeline ·{" "}
            {health?.status === "ok" ? "Backend live" : "Backend starting"}
          </p>
        </div>
      </footer>
    </div>
  );
}
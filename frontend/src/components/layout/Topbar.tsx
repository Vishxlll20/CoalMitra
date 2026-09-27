import { useLocation, Link } from "react-router-dom";
import { ArrowUpRight, Search } from "lucide-react";
import { RoleSwitcher } from "./RoleSwitcher";

const TITLES: Record<string, { title: string; sub?: string }> = {
  "/app": { title: "Command Centre" },
  "/app/documents": { title: "Documents", sub: "Uploaded geological reports & scans" },
  "/app/reports": { title: "Reports", sub: "Auto-generated, fully traceable" },
  "/app/insights": { title: "Insights", sub: "Topic drift & terminology" },
  "/app/anomalies": { title: "Anomalies", sub: "Deviation from coalfield baselines" },
  "/app/query": { title: "AI Query", sub: "Ask in English or हिंदी, with citations" },
  "/app/metrics": { title: "Metrics", sub: "Impact tracked against baseline" },
};

export function Topbar() {
  const { pathname } = useLocation();
  const meta = TITLES[pathname] ?? { title: "CoalMitra" };

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between gap-4 border-b border-slate-200/80 bg-paper/80 px-6 backdrop-blur-md">
      <div className="flex items-center gap-3">
        <div>
          <p className="font-display text-[16px] font-semibold text-navy-900 leading-none">{meta.title}</p>
          {meta.sub && <p className="mt-0.5 text-[11.5px] text-ink/45">{meta.sub}</p>}
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button className="hidden items-center gap-2 rounded-md border hairline bg-white px-3 py-1.5 text-[12.5px] text-ink/40 transition-colors hover:text-ink/70 md:flex lg:w-64">
          <Search className="h-3.5 w-3.5" />
          <span>Search coalfields, blocks, seams…</span>
          <kbd className="ml-auto rounded border border-slate-200 px-1 text-[10px] text-ink/35">⌘K</kbd>
        </button>
        <RoleSwitcher />
        <Link
          to="/"
          className="flex items-center gap-1 rounded-md border hairline bg-white px-2.5 py-1.5 text-[12px] font-medium text-ink/60 transition-colors hover:text-navy-900"
        >
          Landing <ArrowUpRight className="h-3 w-3" />
        </Link>
      </div>
    </header>
  );
}
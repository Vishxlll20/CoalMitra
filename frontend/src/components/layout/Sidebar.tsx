import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  FolderOpen,
  FileText,
  Cloud,
  AlertTriangle,
  MessageSquareText,
  Gauge,
  FlaskConical,
} from "lucide-react";
import { cn } from "../../lib/utils";
import { ROLES, useRoleStore } from "../../stores/role";
import type { Role } from "../../types";

const NAV = [
  { to: "/app", label: "Dashboard", icon: LayoutDashboard, end: true, roles: ["GEOLOGIST", "MINISTRY_OFFICIAL", "AUDITOR"] },
  { to: "/app/documents", label: "Documents", icon: FolderOpen, end: false, roles: ["GEOLOGIST", "AUDITOR"] },
  { to: "/app/reports", label: "Reports", icon: FileText, end: false, roles: ["GEOLOGIST", "MINISTRY_OFFICIAL", "AUDITOR"] },
  { to: "/app/insights", label: "Insights", icon: Cloud, end: false, roles: ["GEOLOGIST", "MINISTRY_OFFICIAL", "AUDITOR"] },
  { to: "/app/anomalies", label: "Anomalies", icon: AlertTriangle, end: false, roles: ["GEOLOGIST", "AUDITOR"] },
  { to: "/app/query", label: "AI Query", icon: MessageSquareText, end: false, roles: ["GEOLOGIST", "MINISTRY_OFFICIAL"] },
  { to: "/app/metrics", label: "Metrics", icon: Gauge, end: false, roles: ["GEOLOGIST", "MINISTRY_OFFICIAL", "AUDITOR"] },
];

export function Sidebar() {
  const role = useRoleStore((s) => s.role);
  const navigate = useNavigate();
  const meta = ROLES.find((r) => r.key === role)!;

  return (
    <aside className="fixed inset-y-0 left-0 z-40 flex w-[232px] flex-col bg-navy-950 text-slate-300/80">
      {/* Brand */}
      <div className="flex items-center gap-3 px-5 pt-6 pb-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gold-500 text-navy-950 font-display font-bold text-lg">
          C
        </div>
        <div>
          <p className="font-display text-[15px] font-semibold tracking-tight text-white">CoalMitra</p>
          <p className="text-[10.5px] uppercase tracking-[0.16em] text-gold-500/80">CMPDIL · CIL</p>
        </div>
      </div>

      {/* Role chip */}
      <button
        onClick={() => navigate("/app")}
        className="mx-4 mb-5 flex items-center gap-2.5 rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-left transition-colors hover:bg-white/[0.07]"
      >
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-gold-500/20 text-gold-400 text-[11px] font-bold">
          {meta.label[0]}
        </span>
        <span className="min-w-0">
          <span className="block truncate text-[12.5px] font-semibold text-white">{meta.label}</span>
          <span className="block truncate text-[10.5px] text-slate-400">{meta.blurb}</span>
        </span>
      </button>

      {/* Nav */}
      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3">
        {NAV.filter((item) => (item.roles as readonly Role[]).includes(role)).map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "group flex items-center gap-3 rounded-md px-3 py-2 text-[13px] font-medium transition-all",
                isActive
                  ? "bg-gold-500/15 text-gold-400 shadow-[inset_2px_0_0_0_theme(colors.gold.500)]"
                  : "text-slate-400 hover:bg-white/[0.05] hover:text-slate-200"
              )
            }
          >
            <Icon className="h-[17px] w-[17px]" strokeWidth={1.8} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="mx-4 mb-5 rounded-lg border border-white/[0.06] bg-white/[0.03] p-3">
        <div className="flex items-center gap-2">
          <FlaskConical className="h-3.5 w-3.5 text-gold-500" />
          <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">CMPDI · CIL</p>
        </div>
        <p className="mt-1 text-[11px] leading-snug text-slate-500">
          Document intelligence workspace
        </p>
      </div>
    </aside>
  );
}
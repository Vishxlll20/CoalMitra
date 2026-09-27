import { Check, ChevronDown } from "lucide-react";
import { useState } from "react";
import { ROLES, useRoleStore } from "../../stores/role";
import { cn } from "../../lib/utils";

/** Demo role switcher — three personas, instant swap, no real auth. */
export function RoleSwitcher() {
  const role = useRoleStore((s) => s.role);
  const setRole = useRoleStore((s) => s.setRole);
  const [open, setOpen] = useState(false);
  const meta = ROLES.find((r) => r.key === role)!;

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-md border hairline bg-white px-3 py-1.5 text-[12.5px] font-medium text-ink shadow-sm transition-colors hover:border-navy-600/30"
      >
        <span className={cn("h-1.5 w-1.5 rounded-full", role === "MINISTRY_OFFICIAL" ? "bg-gold-500" : role === "AUDITOR" ? "bg-info" : "bg-success")} />
        {meta.label}
        <ChevronDown className={cn("h-3.5 w-3.5 text-ink/40 transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 z-50 mt-1.5 w-64 rounded-lg border hairline bg-white p-1.5 shadow-lift animate-rise">
            <p className="px-2.5 py-1.5 text-[10.5px] font-semibold uppercase tracking-[0.14em] text-ink/40">
              View as
            </p>
            {ROLES.map((r) => (
              <button
                key={r.key}
                onClick={() => {
                  setRole(r.key);
                  setOpen(false);
                }}
                className={cn(
                  "flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-left transition-colors",
                  r.key === role ? "bg-gold-100/70" : "hover:bg-paper-warm"
                )}
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-navy-900/5 text-[10.5px] font-bold text-navy-700">
                  {r.label[0]}
                </span>
                <span className="min-w-0">
                  <span className="block text-[13px] font-semibold text-navy-900">{r.label}</span>
                  <span className="block truncate text-[11px] text-ink/50">{r.blurb}</span>
                </span>
                {r.key === role && <Check className="ml-auto h-4 w-4 text-gold-600" />}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
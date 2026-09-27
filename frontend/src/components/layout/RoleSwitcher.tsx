import { LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { ROLES, useRoleStore } from "../../stores/role";
import { useAuthStore } from "../../stores/auth";

/** Shows the authenticated role and provides a session sign-out action. */
export function RoleSwitcher() {
  const role = useRoleStore((s) => s.role);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const meta = ROLES.find((r) => r.key === role)!;

  return (
    <div className="flex items-center gap-2 rounded-md border hairline bg-white px-2.5 py-1.5 shadow-sm">
      <span className={`h-1.5 w-1.5 rounded-full ${role === "MINISTRY_OFFICIAL" ? "bg-gold-500" : role === "AUDITOR" ? "bg-info" : "bg-success"}`} />
      <span className="max-w-36 truncate text-[12px] font-medium text-ink" title={user?.email}>{meta.label}</span>
      <button
        type="button"
        title="Sign out"
        aria-label="Sign out"
        onClick={async () => {
          try { await logout(); } catch { /* local session is cleared in the store */ }
          navigate("/login", { replace: true });
        }}
        className="ml-1 rounded p-1 text-ink/45 transition-colors hover:bg-slate-100 hover:text-navy-900"
      >
        <LogOut className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
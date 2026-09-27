import { useEffect, type ReactNode } from "react";
import { Link, Navigate, Outlet, useLocation } from "react-router-dom";
import type { Role } from "../../types";
import { useAuthStore } from "../../stores/auth";

export function RequireAuth() {
  const user = useAuthStore((state) => state.user);
  const loading = useAuthStore((state) => state.loading);
  const initialize = useAuthStore((state) => state.initialize);
  const location = useLocation();

  useEffect(() => {
    void initialize();
  }, [initialize]);

  if (loading) {
    return <div className="grid min-h-screen place-items-center bg-paper text-[13px] text-ink/55">Checking your session…</div>;
  }
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  return <Outlet />;
}

export function RequireRole({ allowed, children }: { allowed: Role[]; children: ReactNode }) {
  const user = useAuthStore((state) => state.user);
  if (!user || !allowed.includes(user.role)) {
    return <section className="mx-auto mt-16 max-w-lg border-y border-slate-200 py-8 text-center">
      <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-danger">Access restricted</p>
      <h1 className="mt-2 font-display text-[22px] font-semibold text-navy-950">This view is not assigned to your role</h1>
      <p className="mt-2 text-[13px] text-ink/55">Your account remains signed in. Return to the dashboard for the tools available to you.</p>
      <Link to="/app" className="mt-5 inline-flex rounded-md bg-navy-950 px-4 py-2 text-[12px] font-semibold text-white hover:bg-navy-800">Return to dashboard</Link>
    </section>;
  }
  return children;
}

import { useEffect, useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { api } from "../lib/api";
import { ROLES } from "../stores/role";
import { useAuthStore } from "../stores/auth";
import type { DemoAccount } from "../types";

type AuthMode = "login" | "register";

export function AuthPage({ mode }: { mode: AuthMode }) {
  const user = useAuthStore((state) => state.user);
  const login = useAuthStore((state) => state.login);
  const register = useAuthStore((state) => state.register);
  const initialize = useAuthStore((state) => state.initialize);
  const navigate = useNavigate();
  const location = useLocation();
  const [accounts, setAccounts] = useState<DemoAccount[]>([]);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void initialize();
    api.auth.demoAccounts().then(setAccounts).catch(() => setAccounts([]));
  }, [initialize]);

  if (user) return <Navigate to="/app" replace />;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "register") await register(name.trim(), email.trim(), password);
      else await login(email.trim(), password);
      const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
      navigate(from?.startsWith("/app") ? from : "/app", { replace: true });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not authenticate. Try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-paper text-ink">
      <div className="grid min-h-screen lg:grid-cols-[minmax(0,1fr)_minmax(420px,0.82fr)]">
        <section className="relative hidden overflow-hidden bg-navy-950 px-12 py-10 text-white lg:flex lg:flex-col lg:justify-between xl:px-20">
          <div className="absolute inset-0 opacity-[0.08]" style={{ backgroundImage: "linear-gradient(rgba(255,255,255,.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.5) 1px, transparent 1px)", backgroundSize: "48px 48px" }} />
          <Link to="/" className="relative flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-md bg-gold-500 font-display text-xl font-bold text-navy-950">C</span>
            <span>
              <span className="block font-display text-[16px] font-semibold">CoalMitra</span>
              <span className="block text-[10px] uppercase tracking-[0.16em] text-gold-400">CMPDIL · CIL</span>
            </span>
          </Link>
          <div className="relative max-w-xl pb-12">
            <p className="mb-5 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-gold-400">
              <ShieldCheck className="h-4 w-4" /> Verified access · role-aware workspace
            </p>
            <h1 className="font-display text-[42px] font-semibold leading-[1.08]">Every coal record,<br />accountable to its source.</h1>
            <p className="mt-5 max-w-md text-[14px] leading-6 text-slate-300/75">Sign in to review geological records, prepare official answers, or audit source-level evidence with the permissions assigned to your role.</p>
            <div className="mt-10 grid grid-cols-3 gap-3 border-t border-white/10 pt-5">
              {ROLES.map((role) => <div key={role.key}><p className="text-[11px] font-semibold text-white">{role.label}</p><p className="mt-1 text-[10.5px] leading-4 text-slate-400">{role.blurb}</p></div>)}
            </div>
          </div>
          <p className="relative text-[10.5px] text-slate-500">Smart India Hackathon · Problem Statement 26023</p>
        </section>

        <section className="flex min-h-screen flex-col px-5 py-6 sm:px-10 lg:px-14 xl:px-20">
          <div className="flex items-center justify-between lg:justify-end">
            <Link to="/" className="flex items-center gap-2 lg:hidden">
              <span className="flex h-8 w-8 items-center justify-center rounded-md bg-gold-500 font-display font-bold text-navy-950">C</span>
              <span className="font-display text-[14px] font-semibold text-navy-900">CoalMitra</span>
            </Link>
            <Link to="/" className="text-[12px] font-medium text-ink/50 hover:text-navy-900">Back to overview</Link>
          </div>

          <div className="mx-auto flex w-full max-w-[420px] flex-1 flex-col justify-center py-10">
            <p className="text-[10.5px] font-semibold uppercase tracking-[0.16em] text-gold-700">Secure workspace</p>
            <h2 className="mt-2 font-display text-[30px] font-semibold text-navy-950">{mode === "login" ? "Welcome back" : "Create your account"}</h2>
            <p className="mt-2 text-[13px] leading-5 text-ink/55">{mode === "login" ? "Sign in with your CoalMitra account to continue." : "New accounts are assigned the Geologist role. Role changes require an administrator."}</p>

            <form onSubmit={submit} className="mt-7 space-y-4">
              {mode === "register" && <label className="block text-[12px] font-semibold text-ink/75">Full name<input required autoComplete="name" minLength={2} maxLength={120} value={name} onChange={(event) => setName(event.target.value)} className="mt-1.5 block h-11 w-full rounded-md border border-slate-300 bg-white px-3 text-[13px] font-normal text-ink outline-none transition focus:border-gold-600 focus:ring-2 focus:ring-gold-500/20" /></label>}
              <label className="block text-[12px] font-semibold text-ink/75">Work email<input required type="email" autoComplete="email" maxLength={254} value={email} onChange={(event) => setEmail(event.target.value)} className="mt-1.5 block h-11 w-full rounded-md border border-slate-300 bg-white px-3 text-[13px] font-normal text-ink outline-none transition focus:border-gold-600 focus:ring-2 focus:ring-gold-500/20" /></label>
              <label className="block text-[12px] font-semibold text-ink/75">Password<input required type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} minLength={mode === "register" ? 10 : 1} maxLength={256} value={password} onChange={(event) => setPassword(event.target.value)} className="mt-1.5 block h-11 w-full rounded-md border border-slate-300 bg-white px-3 text-[13px] font-normal text-ink outline-none transition focus:border-gold-600 focus:ring-2 focus:ring-gold-500/20" />{mode === "register" && <span className="mt-1 block text-[10.5px] font-normal text-ink/45">Use at least 10 characters.</span>}</label>
              {error && <p role="alert" className="rounded-md border border-danger/20 bg-danger/5 px-3 py-2 text-[12px] text-danger">{error}</p>}
              <button type="submit" disabled={busy} className="flex h-11 w-full items-center justify-center gap-2 rounded-md bg-navy-950 px-4 text-[13px] font-semibold text-white transition hover:bg-navy-800 disabled:cursor-wait disabled:opacity-60">
                {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create Geologist account"}<ArrowRight className="h-4 w-4" />
              </button>
            </form>

            <p className="mt-5 text-center text-[12px] text-ink/55">{mode === "login" ? "New to CoalMitra?" : "Already have an account?"} <Link className="font-semibold text-navy-800 underline decoration-gold-500/70 underline-offset-4" to={mode === "login" ? "/register" : "/login"}>{mode === "login" ? "Create an account" : "Sign in"}</Link></p>

            {mode === "login" && accounts.length > 0 && <div className="mt-8 border-t border-slate-200 pt-5">
              <div className="flex items-center justify-between"><p className="text-[10.5px] font-semibold uppercase tracking-[0.12em] text-ink/45">Demo sign-in</p><span className="rounded-sm bg-success/10 px-1.5 py-0.5 text-[9.5px] font-semibold text-success">DEMO MODE</span></div>
              <div className="mt-2 divide-y divide-slate-100">
                {accounts.map((account) => <button key={account.role} type="button" onClick={() => { setEmail(account.email); setPassword(account.password); setError(""); }} className="flex w-full items-center justify-between gap-3 py-2.5 text-left hover:bg-white">
                  <span><span className="block text-[12px] font-semibold text-navy-900">{ROLES.find((role) => role.key === account.role)?.label}</span><span className="block text-[10.5px] text-ink/45">{account.email}</span></span>
                  <span className="text-[10.5px] font-semibold text-gold-700">Use account</span>
                </button>)}
              </div>
            </div>}
          </div>
          <p className="text-center text-[10px] text-ink/35">Workspace access is restricted by your assigned role.</p>
        </section>
      </div>
    </main>
  );
}

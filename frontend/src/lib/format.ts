/** Number/text formatting helpers tuned for Indian numerals (lakh, crore). */

const IN_LOCALE = "en-IN";

export function fmtNum(n: number | null | undefined, digits = 0): string {
  if (n == null || Number.isNaN(n)) return "—";
  return n.toLocaleString(IN_LOCALE, { maximumFractionDigits: digits });
}

export function fmtMoney(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  return "₹" + n.toLocaleString(IN_LOCALE, { maximumFractionDigits: 0 });
}

export function fmtPct(n: number | null | undefined, digits = 1): string {
  if (n == null || Number.isNaN(n)) return "—";
  return `${n.toFixed(digits)}%`;
}

export function fmtCompact(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  if (Math.abs(n) >= 1e7) return fmtNum(n / 1e7, 1) + " cr";
  if (Math.abs(n) >= 1e5) return fmtNum(n / 1e5, 1) + " L";
  return fmtNum(n);
}

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso.length === 10 ? iso + "T00:00:00" : iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(IN_LOCALE, { day: "numeric", month: "short", year: "numeric" });
}

export function fmtBytes(n: number | null | undefined): string {
  if (n == null || n === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.min(units.length - 1, Math.floor(Math.log(n) / Math.log(1024)));
  return `${(n / 1024 ** i).toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

export function timeAgo(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days}d ago`;
  return fmtDate(iso);
}

/** Lab-style confidence → tone + ring for chips/gauges. */
export function confidenceTone(c: number): "high" | "mid" | "low" {
  if (c >= 0.85) return "high";
  if (c >= 0.65) return "mid";
  return "low";
}

const SEVERITY_TONES: Record<string, string> = {
  LOW: "text-success bg-success/10 border-success/20",
  MEDIUM: "text-info bg-info/10 border-info/20",
  HIGH: "text-gold-600 bg-gold-100 border-gold-500/30",
  CRITICAL: "text-danger bg-danger/10 border-danger/20",
};

export function severityClass(s: string): string {
  return SEVERITY_TONES[s] ?? SEVERITY_TONES.LOW;
}
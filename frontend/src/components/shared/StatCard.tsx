import { cn } from "../../lib/utils";
import { motion } from "framer-motion";

interface StatCardProps {
  label: string;
  value: React.ReactNode;
  hint?: React.ReactNode;
  icon?: React.ReactNode;
  tone?: "default" | "gold" | "green" | "red" | "blue" | "navy";
  trend?: "up" | "down" | "flat";
  className?: string;
}

const iconTones: Record<string, string> = {
  default: "bg-paper-warm text-navy-700",
  gold: "bg-gold-100 text-gold-600",
  green: "bg-success/10 text-success",
  red: "bg-danger/10 text-danger",
  blue: "bg-info/10 text-info",
  navy: "bg-navy-900 text-gold-400",
};

const trendGlyph = { up: "▲", down: "▼", flat: "◆" };
const trendClass = { up: "text-success", down: "text-danger", flat: "text-ink/40" };

export function StatCard({ label, value, hint, icon, tone = "default", trend, className }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className={cn("card p-4.5 p-5", className)}
    >
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <p className="text-[11.5px] font-semibold uppercase tracking-[0.1em] text-ink/45">{label}</p>
          <motion.div
            className="mt-1.5 font-display text-[30px] font-semibold text-navy-900 leading-none tracking-tight"
          >
            {value}
          </motion.div>
          {trend && (
            <span className={cn("mt-1 inline-flex items-center gap-1 text-[11.5px] font-semibold", trendClass[trend])}>
              <span className="text-[9px]">{trendGlyph[trend]}</span> {hint}
            </span>
          )}
          {!trend && hint && <p className="mt-1 text-[12px] text-ink/50">{hint}</p>}
        </div>
        {icon && (
          <div className={cn("shrink-0 rounded-lg p-2", iconTones[tone])}>{icon}</div>
        )}
      </div>
    </motion.div>
  );
}
import { cn } from "../../lib/utils";

/** Designed empty state — icon, title, copy, optional action. */
export function EmptyState({
  icon,
  title,
  copy,
  action,
  className,
}: {
  icon?: React.ReactNode;
  title: string;
  copy?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-slate-300/80 bg-white/50 px-8 py-14 text-center", className)}>
      {icon && (
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-paper-warm border border-slate-200 text-navy-600">
          {icon}
        </div>
      )}
      <div>
        <p className="font-display text-base font-semibold text-navy-900">{title}</p>
        {copy && <p className="mx-auto mt-1 max-w-sm text-[13px] text-ink/55">{copy}</p>}
      </div>
      {action}
    </div>
  );
}
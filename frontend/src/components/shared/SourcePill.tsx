import * as React from "react";
import { ExternalLink } from "lucide-react";
import { cn } from "../../lib/utils";
import { useTraceStore, refKey } from "../../stores/traceability";
import type { SourceRef } from "../../types";

interface SourcePillProps extends React.HTMLAttributes<HTMLButtonElement> {
  refData: SourceRef;
  origin: "report" | "field" | "chat" | "anomaly" | "export";
  label?: React.ReactNode;
}

/**
 * Any clickable number/value in the app. Carries { document_id, page, bbox,
 * confidence } and dispatches a trace focus → SourcePanelHost slides in and
 * pulses the exact region on the source PDF page.
 */
export const SourcePill = React.forwardRef<HTMLButtonElement, SourcePillProps>(
  ({ refData, origin, label, className, onClick, ...props }, ref) => {
    const focusRef = useTraceStore((s) => s.focusRef);
    const activeRefKey = useTraceStore((s) => s.activeRefKey);
    const key = refKey(refData);
    const active = activeRefKey === key;

    return (
      <button
        ref={ref}
        data-trace-key={key}
        onMouseEnter={() => useTraceStore.getState().hoverRef(key)}
        onMouseLeave={() => useTraceStore.getState().hoverRef(null)}
        onClick={(e) => {
          focusRef(refData, origin);
          onClick?.(e);
        }}
        className={cn(
          "group inline-flex items-center gap-1.5 rounded-md px-1.5 py-0.5 text-[14px] font-semibold text-gold-600",
          "underline decoration-gold-500/40 decoration-dotted underline-offset-2",
          "transition-all hover:bg-gold-100/70 hover:decoration-solid",
          active && "bg-gold-100 shadow-glow decoration-solid",
          className
        )}
        title="Click to trace this value to its source document"
        {...props}
      >
        {label}
        <ExternalLink className="h-3 w-3 opacity-0 transition-opacity group-hover:opacity-70" />
      </button>
    );
  }
);
SourcePill.displayName = "SourcePill";
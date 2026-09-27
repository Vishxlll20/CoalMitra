import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11.5px] font-semibold tracking-wide",
  {
    variants: {
      tone: {
        neut: "bg-slate-100 text-slate-700 border border-slate-200",
        navy: "bg-navy-900 text-paper",
        gold: "bg-gold-100 text-amber-soft border border-gold-500/30",
        green: "bg-success/10 text-success border border-success/20",
        blue: "bg-info/10 text-info border border-info/20",
        red: "bg-danger/10 text-danger border border-danger/20",
        outline: "border hairline bg-white text-ink/70",
      },
    },
    defaultVariants: { tone: "neut" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, tone, ...props }, ref) => (
    <span ref={ref} className={cn(badgeVariants({ tone }), className)} {...props} />
  )
);
Badge.displayName = "Badge";

export { Badge, badgeVariants };
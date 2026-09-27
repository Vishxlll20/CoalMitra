import * as React from "react";
import { cn } from "../../lib/utils";
import { motion } from "framer-motion";

interface PageHeaderProps {
  title: React.ReactNode;
  description?: React.ReactNode;
  eyebrow?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

/** Consistent section opener across every page. */
export function PageHeader({ title, description, eyebrow, actions, className }: PageHeaderProps) {
  return (
    <div className={cn("flex flex-wrap items-end justify-between gap-4", className)}>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
        className="max-w-2xl"
      >
        {eyebrow && (
          <div className="mb-1.5 flex items-center gap-2 text-[11.5px] font-semibold uppercase tracking-[0.14em] text-gold-600">
            <span className="h-px w-5 bg-gold-500/60" />
            {eyebrow}
          </div>
        )}
        <h1 className="font-display text-[26px] font-semibold text-navy-900 tracking-tight">
          {title}
        </h1>
        {description && <p className="mt-1.5 text-[14px] text-ink/60 max-w-xl">{description}</p>}
      </motion.div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
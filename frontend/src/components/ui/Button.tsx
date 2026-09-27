import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-500/50 disabled:pointer-events-none disabled:opacity-50 active:translate-y-px",
  {
    variants: {
      variant: {
        default: "bg-navy-900 text-paper hover:bg-navy-800 hover:shadow-md",
        gold: "bg-gold-500 text-navy-950 hover:bg-gold-400 shadow-sm hover:shadow-glow",
        outline: "border hairline bg-white text-ink hover:border-navy-600/40 hover:bg-paper-warm",
        ghost: "text-ink/70 hover:text-ink hover:bg-navy-900/5",
        link: "text-gold-600 underline-offset-4 hover:underline",
        danger: "bg-danger/10 text-danger border border-danger/20 hover:bg-danger/20",
      },
      size: {
        default: "h-9 px-4 text-sm",
        sm: "h-8 px-3 text-[13px]",
        lg: "h-11 px-6 text-[15px]",
        icon: "h-9 w-9",
        iconSm: "h-8 w-8",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />
  )
);
Button.displayName = "Button";

export { Button, buttonVariants };
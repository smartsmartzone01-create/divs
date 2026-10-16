import type { HTMLAttributes } from "react";

export type SectionProps = HTMLAttributes<HTMLElement> & {
  labelledBy?: string;
};

/** Semantic page section with optional accessible heading association. */
export function Section({
  children,
  className,
  labelledBy,
  ...props
}: SectionProps) {
  const classes = ["ui-section", className].filter(Boolean).join(" ");

  return (
    <section
      aria-labelledby={labelledBy}
      className={classes}
      {...props}
    >
      {children}
    </section>
  );
}

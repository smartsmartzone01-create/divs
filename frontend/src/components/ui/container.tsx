import type { HTMLAttributes } from "react";

export type ContainerWidth = "narrow" | "default" | "wide" | "full";

export type ContainerProps = HTMLAttributes<HTMLDivElement> & {
  width?: ContainerWidth;
};

/** Shared responsive content-width wrapper; visual spacing is defined by the design system. */
export function Container({
  children,
  className,
  width = "default",
  ...props
}: ContainerProps) {
  const classes = ["ui-container", `ui-container--${width}`, className]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
}

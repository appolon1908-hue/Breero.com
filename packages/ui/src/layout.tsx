import type { HTMLAttributes, ReactNode } from "react";
import { ChevronRightIcon, HomeIcon } from "./icons";
import { cx } from "./utils";

export function Container({
  size = "xl",
  className,
  ...props
}: HTMLAttributes<HTMLDivElement> & { size?: "sm" | "md" | "lg" | "xl" | "full" }) {
  return <div className={cx("br-container", `br-container--${size}`, className)} {...props} />;
}

export function Section({
  tone = "default",
  spacing = "lg",
  className,
  ...props
}: HTMLAttributes<HTMLElement> & {
  tone?: "default" | "subtle" | "brand" | "dark";
  spacing?: "sm" | "md" | "lg" | "xl";
}) {
  return (
    <section
      className={cx("br-section", `br-section--${tone}`, `br-section--${spacing}`, className)}
      {...props}
    />
  );
}

export function Stack({
  gap = "md",
  align,
  className,
  ...props
}: HTMLAttributes<HTMLDivElement> & {
  gap?: "xs" | "sm" | "md" | "lg" | "xl";
  align?: "start" | "center" | "end" | "stretch";
}) {
  return (
    <div
      className={cx("br-stack", `br-gap--${gap}`, align && `br-align--${align}`, className)}
      {...props}
    />
  );
}

export function Grid({
  columns = 3,
  gap = "md",
  className,
  ...props
}: HTMLAttributes<HTMLDivElement> & { columns?: 1 | 2 | 3 | 4; gap?: "sm" | "md" | "lg" }) {
  return (
    <div className={cx("br-grid", `br-grid--${columns}`, `br-gap--${gap}`, className)} {...props} />
  );
}

export function Breadcrumb({
  items,
  className,
}: {
  items: Array<{ label: string; href?: string }>;
  className?: string;
}) {
  return (
    <nav className={cx("br-breadcrumb", className)} aria-label="Breadcrumb">
      <ol>
        <li>
          <a href="/" aria-label="Home">
            <HomeIcon size={16} />
          </a>
        </li>
        {items.map((item, index) => (
          <li key={`${item.label}-${index}`}>
            <ChevronRightIcon size={14} />
            {item.href && index < items.length - 1 ? (
              <a href={item.href}>{item.label}</a>
            ) : (
              <span aria-current={index === items.length - 1 ? "page" : undefined}>
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}

export function VisuallyHidden({ children }: { children: ReactNode }) {
  return <span className="br-sr-only">{children}</span>;
}

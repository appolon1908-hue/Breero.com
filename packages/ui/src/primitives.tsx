"use client";

import { forwardRef, type ButtonHTMLAttributes, type HTMLAttributes, type ReactNode } from "react";
import { cx } from "./utils";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  leadingIcon?: ReactNode;
  trailingIcon?: ReactNode;
  fullWidth?: boolean;
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  {
    className,
    variant = "primary",
    size = "md",
    loading,
    leadingIcon,
    trailingIcon,
    fullWidth,
    disabled,
    children,
    type = "button",
    ...props
  },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={cx(
        "br-button",
        `br-button--${variant}`,
        `br-button--${size}`,
        fullWidth && "br-button--full",
        className,
      )}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading ? <span className="br-spinner" aria-hidden="true" /> : leadingIcon}
      <span>{loading ? "Please wait" : children}</span>
      {!loading && trailingIcon}
    </button>
  );
});

type IconButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  label: string;
  size?: "sm" | "md" | "lg";
  variant?: "ghost" | "outline" | "primary";
};
export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(function IconButton(
  { label, size = "md", variant = "ghost", className, type = "button", children, ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={cx(
        "br-icon-button",
        `br-icon-button--${size}`,
        `br-icon-button--${variant}`,
        className,
      )}
      aria-label={label}
      title={label}
      {...props}
    >
      {children}
    </button>
  );
});

export function Badge({
  variant = "neutral",
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & {
  variant?: "neutral" | "brand" | "success" | "warning" | "danger";
}) {
  return <span className={cx("br-badge", `br-badge--${variant}`, className)} {...props} />;
}

export function StatusBadge({
  status,
  children,
  className,
}: {
  status: "pending" | "confirmed" | "in-progress" | "completed" | "cancelled";
  children?: ReactNode;
  className?: string;
}) {
  const text = children ?? status.replace("-", " ");
  return (
    <span className={cx("br-status", `br-status--${status}`, className)}>
      <span className="br-status__dot" />
      {text}
    </span>
  );
}

export function Avatar({
  src,
  alt = "",
  name,
  size = "md",
  className,
}: {
  src?: string;
  alt?: string;
  name?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const initials =
    name
      ?.split(/\s+/)
      .slice(0, 2)
      .map((part) => part[0])
      .join("")
      .toUpperCase() || "BR";
  return (
    <span className={cx("br-avatar", `br-avatar--${size}`, className)}>
      {src ? (
        <img src={src} alt={alt || name || "Profile"} />
      ) : (
        <span aria-label={name}>{initials}</span>
      )}
    </span>
  );
}

export function Card({
  interactive,
  className,
  ...props
}: HTMLAttributes<HTMLDivElement> & { interactive?: boolean }) {
  return (
    <div className={cx("br-card", interactive && "br-card--interactive", className)} {...props} />
  );
}

export function Price({
  amount,
  currency = "GBP",
  suffix,
  className,
}: {
  amount: number;
  currency?: string;
  suffix?: string;
  className?: string;
}) {
  return (
    <span className={cx("br-price", className)}>
      {new Intl.NumberFormat("en-GB", {
        style: "currency",
        currency,
        minimumFractionDigits: amount % 1 ? 2 : 0,
      }).format(amount)}
      {suffix && <small>{suffix}</small>}
    </span>
  );
}

import type { CSSProperties, ReactNode } from "react";
import { AlertIcon, SearchIcon } from "./icons";
import { Button } from "./primitives";
import { cx } from "./utils";

export function Skeleton({
  width,
  height = 16,
  rounded = false,
  className,
}: {
  width?: number | string;
  height?: number | string;
  rounded?: boolean;
  className?: string;
}) {
  return (
    <span
      className={cx("br-skeleton", rounded && "br-skeleton--round", className)}
      aria-hidden="true"
      style={{ width, height } as CSSProperties}
    />
  );
}

export function LoadingState({ label = "Loading", rows = 3 }: { label?: string; rows?: number }) {
  return (
    <div className="br-state br-loading" role="status">
      <span className="br-spinner br-spinner--large" />
      <strong>{label}</strong>
      <span className="br-sr-only">Please wait</span>
      <div className="br-loading__lines">
        {Array.from({ length: rows }, (_, index) => (
          <Skeleton key={index} width={`${100 - index * 12}%`} />
        ))}
      </div>
    </div>
  );
}

type StateProps = { title: string; description?: string; action?: ReactNode; className?: string };
export function EmptyState({ title, description, action, className }: StateProps) {
  return (
    <div className={cx("br-state", className)}>
      <span className="br-state__icon">
        <SearchIcon size={26} />
      </span>
      <h2>{title}</h2>
      {description && <p>{description}</p>}
      {action}
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  description = "We couldn't load this right now. Please try again.",
  action,
  onRetry,
  className,
}: StateProps & { onRetry?: () => void }) {
  return (
    <div className={cx("br-state", "br-state--error", className)} role="alert">
      <span className="br-state__icon">
        <AlertIcon size={26} />
      </span>
      <h2>{title}</h2>
      <p>{description}</p>
      {action ||
        (onRetry && (
          <Button variant="outline" onClick={onRetry}>
            Try again
          </Button>
        ))}
    </div>
  );
}

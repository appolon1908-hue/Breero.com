"use client";

import {
  useId,
  useRef,
  useState,
  type HTMLAttributes,
  type KeyboardEvent,
  type ReactNode,
  type TableHTMLAttributes,
} from "react";
import { ChevronRightIcon } from "./icons";
import { IconButton } from "./primitives";
import { cx } from "./utils";

export function Tabs({
  tabs,
  defaultValue,
  value,
  onChange,
  ariaLabel = "Sections",
}: {
  tabs: Array<{ value: string; label: string; content: ReactNode; disabled?: boolean }>;
  defaultValue?: string;
  value?: string;
  onChange?: (value: string) => void;
  ariaLabel?: string;
}) {
  const generated = useId();
  const listRef = useRef<HTMLDivElement>(null);
  const firstEnabled = tabs.find((tab) => !tab.disabled)?.value;
  const [internal, setInternal] = useState(defaultValue || firstEnabled);
  const active = value ?? internal;
  const select = (next: string) => {
    setInternal(next);
    onChange?.(next);
  };
  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    const enabled = tabs.filter((tab) => !tab.disabled);
    if (!enabled.length) return;
    event.preventDefault();
    const current = Math.max(
      0,
      enabled.findIndex((tab) => tab.value === active),
    );
    const nextIndex =
      event.key === "Home"
        ? 0
        : event.key === "End"
          ? enabled.length - 1
          : (current + (event.key === "ArrowRight" ? 1 : -1) + enabled.length) % enabled.length;
    const next = enabled[nextIndex].value;
    select(next);
    requestAnimationFrame(() =>
      listRef.current
        ?.querySelector<HTMLElement>(`#${CSS.escape(`${generated}-${next}-tab`)}`)
        ?.focus(),
    );
  };
  return (
    <div className="br-tabs">
      <div
        ref={listRef}
        className="br-tabs__list"
        role="tablist"
        aria-label={ariaLabel}
        onKeyDown={onKeyDown}
      >
        {tabs.map((tab) => (
          <button
            type="button"
            key={tab.value}
            id={`${generated}-${tab.value}-tab`}
            role="tab"
            aria-selected={active === tab.value}
            aria-controls={`${generated}-${tab.value}-panel`}
            tabIndex={active === tab.value ? 0 : -1}
            disabled={tab.disabled}
            onClick={() => select(tab.value)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {tabs.map((tab) => (
        <div
          key={tab.value}
          id={`${generated}-${tab.value}-panel`}
          role="tabpanel"
          aria-labelledby={`${generated}-${tab.value}-tab`}
          tabIndex={0}
          hidden={active !== tab.value}
        >
          {tab.content}
        </div>
      ))}
    </div>
  );
}

export const Table = ({ className, ...props }: TableHTMLAttributes<HTMLTableElement>) => (
  <div className="br-table-wrap" tabIndex={0}>
    <table className={cx("br-table", className)} {...props} />
  </div>
);
export const TableHeader = (props: HTMLAttributes<HTMLTableSectionElement>) => <thead {...props} />;
export const TableBody = (props: HTMLAttributes<HTMLTableSectionElement>) => <tbody {...props} />;
export const TableRow = (props: HTMLAttributes<HTMLTableRowElement>) => <tr {...props} />;
export const TableHead = (props: HTMLAttributes<HTMLTableCellElement>) => (
  <th scope="col" {...props} />
);
export const TableCell = (props: HTMLAttributes<HTMLTableCellElement>) => <td {...props} />;

export function Pagination({
  page,
  totalPages,
  onChange,
  label = "Pagination",
}: {
  page: number;
  totalPages: number;
  onChange?: (page: number) => void;
  label?: string;
}) {
  const pages = Array.from({ length: totalPages }, (_, index) => index + 1).filter(
    (item) => item === 1 || item === totalPages || Math.abs(item - page) <= 1,
  );
  return (
    <nav className="br-pagination" aria-label={label}>
      <IconButton
        label="Previous page"
        variant="outline"
        disabled={page <= 1}
        onClick={() => onChange?.(page - 1)}
      >
        <ChevronRightIcon className="br-rotate-180" />
      </IconButton>
      {pages.map((item, index) => (
        <span key={item}>
          {index > 0 && item - pages[index - 1] > 1 && <i>…</i>}
          <button
            type="button"
            aria-label={`Page ${item}`}
            aria-current={item === page ? "page" : undefined}
            onClick={() => onChange?.(item)}
          >
            {item}
          </button>
        </span>
      ))}
      <IconButton
        label="Next page"
        variant="outline"
        disabled={page >= totalPages}
        onClick={() => onChange?.(page + 1)}
      >
        <ChevronRightIcon />
      </IconButton>
    </nav>
  );
}

export function Timeline({
  items,
}: {
  items: Array<{
    title: string;
    description?: string;
    time?: string;
    status?: "complete" | "current" | "upcoming";
  }>;
}) {
  return (
    <ol className="br-timeline">
      {items.map((item, index) => (
        <li key={`${item.title}-${index}`} className={`br-timeline--${item.status || "upcoming"}`}>
          <span className="br-timeline__mark" />
          <div>
            <strong>{item.title}</strong>
            {item.time && <time>{item.time}</time>}
            {item.description && <p>{item.description}</p>}
          </div>
        </li>
      ))}
    </ol>
  );
}

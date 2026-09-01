"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import { PortalApiError } from "./api";
import { toRows } from "./api";
import { useSession } from "./session";
import type { PortalAction, PortalColumn, PortalSection, Row } from "./types";

/** Render an unknown scalar without ever printing "[object Object]" at an operator. */
export function formatCell(value: unknown): ReactNode {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value)) return value.length ? `${value.length} items` : "—";
  if (typeof value === "object") return JSON.stringify(value);
  const text = String(value);
  // ISO timestamps are the most common column in this API and are unreadable raw.
  if (/^\d{4}-\d{2}-\d{2}T[\d:.]+/.test(text)) {
    const parsed = new Date(text);
    if (!Number.isNaN(parsed.getTime())) return parsed.toLocaleString();
  }
  return text;
}

/** Columns inferred from the payload, used only when a section declares none. */
export function inferColumns(rows: Row[]): PortalColumn[] {
  if (!rows.length) return [];
  const preferred = ["id", "reference", "status", "created_at", "name", "email"];
  const keys = Object.keys(rows[0]);
  const ordered = [
    ...preferred.filter((key) => keys.includes(key)),
    ...keys.filter((key) => !preferred.includes(key)),
  ];
  return ordered.slice(0, 6).map((key) => ({ key, label: key.replaceAll("_", " ") }));
}

export function BlockedCapability({ section }: { section: PortalSection }) {
  return (
    <div className="portal-blocked" role="note">
      <h3>Not available yet</h3>
      <p>{section.blockedReason}</p>
      {section.blockedOn && (
        <p className="portal-blocked__next">
          <strong>Unblocked by:</strong> {section.blockedOn}
        </p>
      )}
      <p className="portal-blocked__promise">
        No placeholder data is shown here. When this screen has real records, they will be real.
      </p>
    </div>
  );
}

function ActionButton({
  action,
  row,
  onDone,
}: {
  action: PortalAction;
  row: Row;
  onDone: () => void;
}) {
  const { request } = useSession();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function run() {
    if (action.confirm && !globalThis.confirm(action.confirm)) return;
    setBusy(true);
    setError("");
    try {
      await request(action.path(row), {
        method: action.method,
        body: action.body ? action.body(row) : undefined,
      });
      onDone();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <span className="portal-action">
      <button
        type="button"
        className={action.destructive ? "is-destructive" : ""}
        disabled={busy}
        onClick={() => void run()}
      >
        {busy ? "Working…" : action.label}
      </button>
      {error && (
        <span className="portal-error" role="alert">
          {error}
        </span>
      )}
    </span>
  );
}

export function ResourceView({ section }: { section: PortalSection }) {
  const { request, ready } = useSession();
  const [rows, setRows] = useState<Row[] | null>(null);
  const [error, setError] = useState("");
  const [forbidden, setForbidden] = useState(false);

  const load = useCallback(
    async (signal?: AbortSignal) => {
      if (!section.source) return;
      setError("");
      setForbidden(false);
      setRows(null);
      try {
        setRows(toRows(await request<unknown>(section.source, { signal })));
      } catch (reason) {
        if (signal?.aborted) return;
        // A permission failure is not an outage. Saying so stops an operator
        // escalating a missing role as a broken portal.
        if (reason instanceof PortalApiError && reason.isForbidden) {
          setForbidden(true);
          setRows([]);
          return;
        }
        setError(reason instanceof Error ? reason.message : "Unable to load data");
        setRows([]);
      }
    },
    [request, section.source],
  );

  useEffect(() => {
    // Wait for the stored session to be read. Fetching first would send an
    // unauthenticated request, take a 401, and sign the operator straight back out
    // on every page load. The shell gates on `ready` too, but this component must be
    // safe to mount on its own.
    if (!ready) return;
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load, ready]);

  if (!section.source) return <BlockedCapability section={section} />;

  const columns = section.columns?.length ? section.columns : inferColumns(rows ?? []);
  const actions = (section.actions ?? []).filter(Boolean);

  return (
    <div className="portal-resource">
      <div className="portal-resource__bar">
        <button type="button" onClick={() => void load()} className="portal-refresh">
          Refresh
        </button>
      </div>

      {forbidden && (
        <div className="portal-notice" role="note">
          Your account is signed in, but does not hold the permission this screen needs. Ask an
          administrator to grant it rather than retrying.
        </div>
      )}

      {error && (
        <p className="portal-error" role="alert">
          {error}
        </p>
      )}

      {rows === null && <p role="status">Loading live data…</p>}

      {rows !== null && rows.length === 0 && !error && !forbidden && (
        <div className="portal-empty">
          <h3>{section.emptyTitle ?? "Nothing here right now"}</h3>
          <p>
            {section.emptyDescription ??
              "This screen is connected to the live API and currently has no records."}
          </p>
        </div>
      )}

      {rows !== null && rows.length > 0 && (
        <div className="portal-table-wrap">
          <table>
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column.key} className={column.numeric ? "is-numeric" : undefined}>
                    {column.label}
                  </th>
                ))}
                {actions.length > 0 && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={String(row.id ?? row.reference ?? index)}>
                  {columns.map((column) => (
                    <td key={column.key} className={column.numeric ? "is-numeric" : undefined}>
                      {column.render ? column.render(row) : formatCell(row[column.key])}
                    </td>
                  ))}
                  {actions.length > 0 && (
                    <td className="portal-actions">
                      {actions
                        .filter((action) => !action.available || action.available(row))
                        .map((action) => (
                          <ActionButton
                            key={action.label}
                            action={action}
                            row={row}
                            onDone={() => void load()}
                          />
                        ))}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

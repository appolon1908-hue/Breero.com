"use client";

import { type FormEvent, useEffect, useState } from "react";

export type PortalRole = "vendor_admin" | "operations" | "finance" | "admin";
export interface PortalSection {
  label: string;
  path?: string;
  description: string;
}
export interface PortalConfig {
  name: string;
  eyebrow: string;
  canonicalOrigin: string;
  publicOrigin: string;
  supportEmail: string;
  allowedRoles: PortalRole[];
  sections: PortalSection[];
}

type User = { email: string; full_name: string; role: string };
export type PortalSession = {
  access_token: string;
  refresh_token?: string;
  user: User;
};

const SESSION_KEY = "breero-portal-session";

const apiBase = () => {
  const value = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!value || !/^https:\/\//.test(value)) {
    throw new Error("A secure API origin is required");
  }
  return value.replace(/\/$/, "");
};

function decodeJwtExpiry(token: string): number | null {
  const payload = token.split(".")[1];
  if (!payload) return null;
  try {
    const normalized = payload.replaceAll("-", "+").replaceAll("_", "/");
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
    const decoded = JSON.parse(atob(padded)) as { exp?: number };
    return typeof decoded.exp === "number" ? decoded.exp * 1000 : null;
  } catch {
    return null;
  }
}

export function isPortalSessionUsable(session: PortalSession, allowedRoles: PortalRole[]): boolean {
  if (!session.access_token || !session.user || !allowedRoles.includes(session.user.role as PortalRole)) {
    return false;
  }
  const expiresAt = decodeJwtExpiry(session.access_token);
  return expiresAt === null || expiresAt > Date.now();
}

async function request<T>(
  path: string,
  token?: string,
  init?: RequestInit,
  onUnauthorized?: () => void,
): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  if (init?.body) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${apiBase()}${path}`, {
    ...init,
    headers,
    cache: "no-store",
    credentials: "include",
  });

  if (response.status === 401) onUnauthorized?.();

  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { message?: string; detail?: string };
    throw new Error(body.message ?? body.detail ?? `Request failed (${response.status})`);
  }

  return response.status === 204 ? undefined as T : response.json() as Promise<T>;
}

function safeRows(value: unknown): Record<string, unknown>[] {
  if (Array.isArray(value)) {
    return value.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object");
  }
  if (value && typeof value === "object" && "items" in value && Array.isArray((value as { items: unknown }).items)) {
    return (value as { items: unknown[] }).items.filter(
      (item): item is Record<string, unknown> => Boolean(item) && typeof item === "object",
    );
  }
  return value && typeof value === "object" ? [value as Record<string, unknown>] : [];
}

export function PortalApp({ config }: { config: PortalConfig }) {
  const [session, setSession] = useState<PortalSession | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [active, setActive] = useState(config.sections[0]);
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(false);
  const [authBusy, setAuthBusy] = useState(false);
  const [signingOut, setSigningOut] = useState(false);

  const clearSession = (message = "") => {
    window.sessionStorage.removeItem(SESSION_KEY);
    setSession(null);
    setRows([]);
    setError(message);
  };

  useEffect(() => {
    const raw = window.sessionStorage.getItem(SESSION_KEY);
    if (!raw) return;
    try {
      const restored = JSON.parse(raw) as PortalSession;
      if (!isPortalSessionUsable(restored, config.allowedRoles)) {
        window.sessionStorage.removeItem(SESSION_KEY);
        return;
      }
      setSession(restored);
    } catch {
      window.sessionStorage.removeItem(SESSION_KEY);
    }
  }, [config.allowedRoles]);

  async function login(event: FormEvent) {
    event.preventDefault();
    setError("");
    setAuthBusy(true);
    try {
      const next = await request<PortalSession>("/auth/login", undefined, {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      if (!isPortalSessionUsable(next, config.allowedRoles)) {
        throw new Error("This account is not authorized for this portal.");
      }
      window.sessionStorage.setItem(SESSION_KEY, JSON.stringify(next));
      setSession(next);
      setPassword("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Sign in failed");
    } finally {
      setAuthBusy(false);
    }
  }

  async function logout() {
    if (!session || signingOut) return;
    setSigningOut(true);
    try {
      await request<void>(
        "/auth/logout",
        session.access_token,
        {
          method: "POST",
          body: JSON.stringify(session.refresh_token ? { refresh_token: session.refresh_token } : {}),
        },
        () => clearSession("Your session expired. Sign in again."),
      );
    } catch {
      // Local sign-out remains fail-safe when remote revocation is unavailable.
    } finally {
      clearSession();
      setSigningOut(false);
    }
  }

  async function load(section: PortalSection) {
    setActive(section);
    setRows([]);
    setError("");
    if (!section.path || !session) return;
    setLoading(true);
    try {
      setRows(
        safeRows(
          await request<unknown>(
            section.path,
            session.access_token,
            undefined,
            () => clearSession("Your session expired. Sign in again."),
          ),
        ),
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load data");
    } finally {
      setLoading(false);
    }
  }

  if (!session) {
    return (
      <main id="main-content" className="portal-login">
        <section className="portal-login__card" aria-labelledby="login-title">
          <a className="portal-brand" href={config.publicOrigin} aria-label="BREERO home">BREERO</a>
          <span className="portal-domain">{new URL(config.canonicalOrigin).hostname}</span>
          <p className="portal-eyebrow">{config.eyebrow}</p>
          <h1 id="login-title">{config.name}</h1>
          <p>Sign in with an authorized BREERO account. This portal uses the live BREERO API and never displays fixture data.</p>
          <form onSubmit={login} aria-busy={authBusy}>
            <label htmlFor="portal-email">Email
              <input
                id="portal-email"
                type="email"
                autoComplete="username"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>
            <label htmlFor="portal-password">Password
              <input
                id="portal-password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>
            {error && <p className="portal-error" role="alert">{error}</p>}
            <button type="submit" disabled={authBusy}>{authBusy ? "Signing in…" : "Sign in"}</button>
          </form>
          <div className="portal-login__links">
            <a href={config.publicOrigin}>Return to BREERO</a>
            <a href={`mailto:${config.supportEmail}`}>Contact support</a>
          </div>
        </section>
      </main>
    );
  }

  return (
    <div className="portal-shell">
      <aside>
        <a className="portal-brand" href={config.publicOrigin} aria-label="BREERO home">BREERO</a>
        <span className="portal-domain">{new URL(config.canonicalOrigin).hostname}</span>
        <p>{config.name}</p>
        <nav aria-label="Portal navigation">
          {config.sections.map((section) => (
            <button
              key={section.label}
              type="button"
              className={active.label === section.label ? "is-active" : ""}
              onClick={() => void load(section)}
            >
              {section.label}
            </button>
          ))}
        </nav>
        <button className="portal-signout" type="button" disabled={signingOut} onClick={() => void logout()}>
          {signingOut ? "Signing out…" : "Log out"}
        </button>
        <div className="portal-legal">
          <a href={config.publicOrigin}>breero.com</a>
          <a href={`mailto:${config.supportEmail}`}>Support</a>
        </div>
      </aside>
      <main id="main-content">
        <header className="portal-topbar">
          <div>
            <p className="portal-eyebrow">{config.eyebrow}</p>
            <h1>{active.label}</h1>
          </div>
          <p>{session.user.full_name}<br /><small>{session.user.email}</small></p>
        </header>
        <section className="portal-panel">
          <h2>{active.label}</h2>
          <p>{active.description}</p>
          {!active.path && (
            <div className="portal-notice">
              This capability is not exposed by the canonical API yet. No placeholder data is shown.
            </div>
          )}
          {loading && <p role="status">Loading live data…</p>}
          {error && <p className="portal-error" role="alert">{error}</p>}
          {active.path && !loading && !error && rows.length === 0 && (
            <p className="portal-empty">No records are currently available.</p>
          )}
          {rows.length > 0 && (
            <div className="portal-table-wrap">
              <table>
                <thead>
                  <tr>{Object.keys(rows[0]).slice(0, 6).map((key) => <th key={key}>{key.replaceAll("_", " ")}</th>)}</tr>
                </thead>
                <tbody>
                  {rows.map((row, index) => (
                    <tr key={String(row.id ?? index)}>
                      {Object.keys(rows[0]).slice(0, 6).map((key) => (
                        <td key={key}>{typeof row[key] === "object" ? JSON.stringify(row[key]) : String(row[key] ?? "—")}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

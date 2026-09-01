"use client";

import { useState, type FormEvent } from "react";
import { ResourceView } from "./resource-view";
import { SessionProvider, useSession } from "./session";
import type { PortalConfig, PortalSection } from "./types";

function SignIn({ config }: { config: PortalConfig }) {
  const { signIn } = useSession();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await signIn(email, password);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Sign in failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="portal-login">
      <section className="portal-login__card" aria-labelledby="portal-login-title">
        <p className="portal-eyebrow">{config.eyebrow}</p>
        <h1 id="portal-login-title">{config.name}</h1>
        <p>
          Sign in with an authorised BREERO account. This portal reads the live API and never
          displays fixture data.
        </p>
        <form onSubmit={submit}>
          <label>
            Email
            <input
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          {error && (
            <p className="portal-error" role="alert">
              {error}
            </p>
          )}
          <button type="submit" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <a href="https://breero.com">Return to BREERO</a>
      </section>
    </main>
  );
}

function Workspace({
  config,
  section,
  onNavigate,
}: {
  config: PortalConfig;
  section: PortalSection;
  onNavigate: (slug: string) => void;
}) {
  const { session, signOut } = useSession();
  const blockedCount = config.sections.filter((item) => !item.source).length;

  return (
    <div className="portal-shell">
      <aside>
        <a className="portal-brand" href="https://breero.com" aria-label="BREERO home">
          BREERO
        </a>
        <p>{config.name}</p>
        <nav aria-label="Portal navigation">
          {config.sections.map((item) => (
            <button
              key={item.slug}
              type="button"
              className={item.slug === section.slug ? "is-active" : ""}
              aria-current={item.slug === section.slug ? "page" : undefined}
              onClick={() => onNavigate(item.slug)}
            >
              {item.label}
              {/* Marked in the nav so the gap is visible before it is clicked into. */}
              {!item.source && <span className="portal-nav__blocked">not yet</span>}
            </button>
          ))}
        </nav>
        {blockedCount > 0 && (
          <p className="portal-nav__summary">
            {blockedCount} of {config.sections.length} screens are awaiting backend support.
          </p>
        )}
        <button type="button" className="portal-signout" onClick={signOut}>
          Sign out
        </button>
      </aside>
      <main>
        <header>
          <div>
            <p className="portal-eyebrow">{config.eyebrow}</p>
            <h1>{section.label}</h1>
          </div>
          <p>
            {session?.user.full_name}
            <br />
            <small>{session?.user.email}</small>
          </p>
        </header>
        <section className="portal-panel">
          <p className="portal-panel__description">{section.description}</p>
          <ResourceView section={section} />
        </section>
      </main>
    </div>
  );
}

function PortalBody({ config, initialSlug }: { config: PortalConfig; initialSlug?: string }) {
  const { session, ready } = useSession();
  const [slug, setSlug] = useState(initialSlug ?? config.sections[0]!.slug);
  const section = config.sections.find((item) => item.slug === slug) ?? config.sections[0]!;

  // Render nothing rather than the sign-in form while storage is being read, or a
  // signed-in operator sees a login flash on every reload.
  if (!ready) return <main className="portal-login" aria-busy="true" />;
  if (!session) return <SignIn config={config} />;
  return <Workspace config={config} section={section} onNavigate={setSlug} />;
}

export function PortalApp({ config, initialSlug }: { config: PortalConfig; initialSlug?: string }) {
  return (
    <SessionProvider allowedRoles={config.allowedRoles}>
      <PortalBody config={config} initialSlug={initialSlug} />
    </SessionProvider>
  );
}

"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { PortalApiError, portalRequest } from "./api";
import type { PortalRole, PortalSession } from "./types";

const STORAGE_KEY = "breero-portal-session";

interface SessionContextValue {
  session: PortalSession | null;
  ready: boolean;
  signIn(email: string, password: string): Promise<void>;
  signOut(): void;
  /** Request helper that attaches the token and signs out on a 401. */
  request<T>(
    path: string,
    options?: { method?: string; body?: unknown; signal?: AbortSignal },
  ): Promise<T>;
}

const SessionContext = createContext<SessionContextValue | null>(null);

function readStoredSession(): PortalSession | null {
  // sessionStorage, not localStorage: an operator console should not leave a token
  // behind in a closed tab on a shared machine.
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as PortalSession) : null;
  } catch {
    // Corrupt or unavailable storage must not brick the sign-in screen.
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      /* storage is unavailable entirely; sign-in still works in memory */
    }
    return null;
  }
}

export function SessionProvider({
  allowedRoles,
  children,
}: {
  allowedRoles: PortalRole[];
  children: ReactNode;
}) {
  const [session, setSession] = useState<PortalSession | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setSession(readStoredSession());
    setReady(true);
  }, []);

  const signOut = useCallback(() => {
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      /* nothing to clear */
    }
    setSession(null);
  }, []);

  const signIn = useCallback(
    async (email: string, password: string) => {
      const next = await portalRequest<PortalSession>("/auth/login", {
        method: "POST",
        body: { email, password },
      });
      if (!allowedRoles.includes(next.user.role as PortalRole)) {
        // Refuse locally as well as server-side. Storing a token this portal will
        // never accept only produces confusing 403s on every subsequent screen.
        throw new PortalApiError("This account is not authorised for this portal.", 403);
      }
      try {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      } catch {
        /* in-memory session still works for this tab */
      }
      setSession(next);
    },
    [allowedRoles],
  );

  const request = useCallback(
    async <T,>(
      path: string,
      options: { method?: string; body?: unknown; signal?: AbortSignal } = {},
    ): Promise<T> => {
      try {
        return await portalRequest<T>(path, { ...options, token: session?.access_token });
      } catch (error) {
        // An expired token should return the operator to sign-in, not strand them on
        // a screen that reports "unauthorised" for every action they try.
        if (error instanceof PortalApiError && error.isUnauthenticated) signOut();
        throw error;
      }
    },
    [session?.access_token, signOut],
  );

  const value = useMemo<SessionContextValue>(
    () => ({ session, ready, signIn, signOut, request }),
    [session, ready, signIn, signOut, request],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionContextValue {
  const value = useContext(SessionContext);
  if (!value) throw new Error("useSession must be used inside a SessionProvider");
  return value;
}

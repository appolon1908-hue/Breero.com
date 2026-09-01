"use client";

import {
  createBreeroApi,
  createConfiguredApi,
  readPublicApiConfig,
  type AuthSession,
} from "@breero/api-client";
import { bookings, payments, profile, quotes } from "./data";
import { keycloak } from "../keycloak";

const ACCESS_KEY = "breero_access_token";
const REFRESH_KEY = "breero_refresh_token";
let refreshInFlight: Promise<string | null> | null = null;
const publicConfig = {
  NODE_ENV: process.env.NODE_ENV,
  NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
  NEXT_PUBLIC_API_MODE: process.env.NEXT_PUBLIC_API_MODE,
  NEXT_PUBLIC_API_TIMEOUT_MS: process.env.NEXT_PUBLIC_API_TIMEOUT_MS,
  NEXT_PUBLIC_E2E_ALLOW_MOCK: process.env.NEXT_PUBLIC_E2E_ALLOW_MOCK,
  NEXT_PUBLIC_DEPLOYMENT_ENV: process.env.NEXT_PUBLIC_DEPLOYMENT_ENV,
};

export const customerSession = {
  save(session: Pick<AuthSession, "access_token" | "refresh_token">) {
    window.sessionStorage.setItem(ACCESS_KEY, session.access_token);
    if (session.refresh_token) window.sessionStorage.setItem(REFRESH_KEY, session.refresh_token);
  },
  clear() {
    window.sessionStorage.removeItem(ACCESS_KEY);
    window.sessionStorage.removeItem(REFRESH_KEY);
  },
  accessToken: () =>
    typeof window === "undefined" ? null : window.sessionStorage.getItem(ACCESS_KEY),
  async refresh(): Promise<string | null> {
    if (refreshInFlight) return refreshInFlight;
    refreshInFlight = (async () => {
      const refreshToken = window.sessionStorage.getItem(REFRESH_KEY);
      if (!refreshToken) return null;
      try {
        if (keycloak.enabled) {
          const session = await keycloak.refresh(refreshToken);
          customerSession.save(session);
          return session.access_token;
        }
        const config = readPublicApiConfig({ ...publicConfig, NEXT_PUBLIC_API_MODE: "live" });
        const api = createBreeroApi({ baseUrl: config.apiBaseUrl, timeoutMs: config.timeoutMs });
        const session = await api.auth.refresh({ refresh_token: refreshToken });
        customerSession.save(session);
        return session.access_token;
      } catch {
        customerSession.clear();
        return null;
      } finally {
        refreshInFlight = null;
      }
    })();
    return refreshInFlight;
  },
};

export const customerApi = createConfiguredApi(publicConfig, {
  getAccessToken: customerSession.accessToken,
  refreshAccessToken: customerSession.refresh,
  onUnauthorized: () => {
    customerSession.clear();
    window.location.assign("/account/session-expired");
  },
  mock: { bookings, payments, profile, quotes, latencyMs: 450 },
});

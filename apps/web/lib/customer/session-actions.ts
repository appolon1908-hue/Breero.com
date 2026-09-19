"use client";

import { customerApi, customerSession } from "@/lib/customer/api";
import { keycloak } from "@/lib/keycloak";

const REFRESH_KEY = "breero_refresh_token";
export const CUSTOMER_SESSION_EVENT = "breero:customer-session-change";

function isExpiredJwt(token: string): boolean {
  const payload = token.split(".")[1];
  if (!payload) return false;

  try {
    const normalized = payload.replaceAll("-", "+").replaceAll("_", "/");
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
    const decoded = JSON.parse(atob(padded)) as { exp?: number };
    return typeof decoded.exp === "number" && decoded.exp * 1000 <= Date.now();
  } catch {
    // Opaque access tokens are still supported; the API remains authoritative.
    return false;
  }
}

export function hasCustomerSession(): boolean {
  const token = customerSession.accessToken();
  if (!token) return false;
  if (!isExpiredJwt(token)) return true;

  customerSession.clear();
  notifyCustomerSessionChanged();
  return false;
}

export function notifyCustomerSessionChanged(): void {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(CUSTOMER_SESSION_EVENT));
  }
}

/**
 * Performs provider/API logout before clearing the local session.
 * Local sign-out is fail-safe: an unavailable revocation endpoint does not
 * leave browser credentials behind.
 */
export async function logoutCustomerSession(redirectTo = "/account/login"): Promise<void> {
  if (typeof window === "undefined") return;

  if (keycloak.enabled) {
    customerSession.clear();
    notifyCustomerSessionChanged();
    keycloak.logout();
    return;
  }

  const refreshToken = window.sessionStorage.getItem(REFRESH_KEY);

  try {
    if (refreshToken) {
      await customerApi.auth.logout({ refresh_token: refreshToken });
    }
  } catch {
    // The browser session must still be cleared when remote revocation is unavailable.
  } finally {
    customerSession.clear();
    notifyCustomerSessionChanged();
    window.location.assign(redirectTo);
  }
}

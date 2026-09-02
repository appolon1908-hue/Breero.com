"use client";

import { customerApi, customerSession } from "@/lib/customer/api";
import { keycloak } from "@/lib/keycloak";

const REFRESH_KEY = "breero_refresh_token";
export const CUSTOMER_SESSION_EVENT = "breero:customer-session-change";

export function hasCustomerSession(): boolean {
  return Boolean(customerSession.accessToken());
}

export function notifyCustomerSessionChanged(): void {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(CUSTOMER_SESSION_EVENT));
  }
}

/**
 * Performs provider/API logout before clearing the local session.
 * The caller supplies the post-logout route so public and account shells can
 * share one durable logout implementation.
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
  } finally {
    customerSession.clear();
    notifyCustomerSessionChanged();
    window.location.assign(redirectTo);
  }
}

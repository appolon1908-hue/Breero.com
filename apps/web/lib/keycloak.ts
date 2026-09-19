const enabled = process.env.NEXT_PUBLIC_KEYCLOAK_ENABLED === "true";
const apiBase = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1").replace(/\/$/, "");

function csrfToken(): string {
  const value = document.cookie.split("; ").find((item) => item.startsWith("breero_csrf="));
  return value ? decodeURIComponent(value.split("=")[1] ?? "") : "";
}

export const keycloak = {
  enabled,
  async login(returnTo = "/account") {
    if (!enabled) throw new Error("Keycloak login is unavailable");
    window.location.assign(`${apiBase}/auth/keycloak/login?return_to=${encodeURIComponent(returnTo)}`);
  },
  async logout() {
    const response = await fetch(`${apiBase}/auth/keycloak/logout`, {
      method: "POST",
      credentials: "include",
      headers: { "X-CSRF-Token": csrfToken() },
    });
    if (!response.ok && response.status !== 401) throw new Error("Logout failed");
    if (response.ok) {
      const body = (await response.json()) as { end_session_url?: string };
      if (body.end_session_url) {
        window.location.assign(body.end_session_url);
        return;
      }
    }
    window.location.assign("/");
  },
};

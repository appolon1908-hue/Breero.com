const issuer = process.env.NEXT_PUBLIC_KEYCLOAK_ISSUER?.replace(/\/$/, "") ?? "";
const clientId = process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID ?? "breero-web-production";
const enabled = process.env.NEXT_PUBLIC_KEYCLOAK_ENABLED === "true";

const VERIFIER_KEY = "breero_oidc_verifier";
const STATE_KEY = "breero_oidc_state";
const RETURN_TO_KEY = "breero_oidc_return_to";

const base64url = (bytes: Uint8Array) =>
  btoa(String.fromCharCode(...bytes))
    .replaceAll("+", "-")
    .replaceAll("/", "_")
    .replaceAll("=", "");

const safeInternalPath = (value: string | null | undefined, fallback = "/account") =>
  value && value.startsWith("/") && !value.startsWith("//") ? value : fallback;

export const keycloak = {
  enabled,
  issuer,
  clientId,
  async login(returnTo = "/account") {
    if (!enabled || !issuer) throw new Error("Keycloak login is unavailable");
    const verifier = base64url(crypto.getRandomValues(new Uint8Array(48)));
    const challenge = base64url(
      new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier))),
    );
    const state = base64url(crypto.getRandomValues(new Uint8Array(24)));
    sessionStorage.setItem(VERIFIER_KEY, verifier);
    sessionStorage.setItem(STATE_KEY, state);
    sessionStorage.setItem(RETURN_TO_KEY, safeInternalPath(returnTo));
    const redirectUri = `${window.location.origin}/account/callback`;
    const query = new URLSearchParams({
      client_id: clientId,
      redirect_uri: redirectUri,
      response_type: "code",
      scope: "openid profile email",
      state,
      code_challenge: challenge,
      code_challenge_method: "S256",
    });
    window.location.assign(`${issuer}/protocol/openid-connect/auth?${query}`);
  },
  async exchange(code: string, state: string) {
    const expected = sessionStorage.getItem(STATE_KEY);
    const verifier = sessionStorage.getItem(VERIFIER_KEY);
    sessionStorage.removeItem(STATE_KEY);
    sessionStorage.removeItem(VERIFIER_KEY);
    if (!expected || !verifier || state !== expected) throw new Error("Invalid login state");
    const response = await fetch(`${issuer}/protocol/openid-connect/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "authorization_code",
        client_id: clientId,
        code,
        redirect_uri: `${window.location.origin}/account/callback`,
        code_verifier: verifier,
      }),
    });
    if (!response.ok) throw new Error("Login exchange failed");
    return response.json() as Promise<{
      access_token: string;
      refresh_token?: string;
      id_token?: string;
    }>;
  },
  consumeReturnTo() {
    const returnTo = safeInternalPath(sessionStorage.getItem(RETURN_TO_KEY));
    sessionStorage.removeItem(RETURN_TO_KEY);
    return returnTo;
  },
  async refresh(refreshToken: string) {
    const response = await fetch(`${issuer}/protocol/openid-connect/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "refresh_token",
        client_id: clientId,
        refresh_token: refreshToken,
      }),
    });
    if (!response.ok) throw new Error("Session refresh failed");
    return response.json() as Promise<{ access_token: string; refresh_token?: string }>;
  },
  logout(postLogoutPath = "/") {
    sessionStorage.removeItem(VERIFIER_KEY);
    sessionStorage.removeItem(STATE_KEY);
    sessionStorage.removeItem(RETURN_TO_KEY);
    const query = new URLSearchParams({
      client_id: clientId,
      post_logout_redirect_uri: `${window.location.origin}${safeInternalPath(postLogoutPath, "/")}`,
    });
    window.location.assign(`${issuer}/protocol/openid-connect/logout?${query}`);
  },
};

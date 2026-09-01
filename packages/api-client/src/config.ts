export interface PublicApiConfig {
  apiBaseUrl: string;
  mode: "live" | "mock";
  timeoutMs: number;
}

export function readPublicApiConfig(env: Record<string, string | undefined>): PublicApiConfig {
  const apiBaseUrl =
    env.NEXT_PUBLIC_API_BASE_URL ??
    (env.NODE_ENV === "production"
      ? "https://api.breero.com/api/v1"
      : "http://localhost:8000/api/v1");
  const mode = env.NEXT_PUBLIC_API_MODE === "mock" ? "mock" : "live";
  const timeoutMs = Number(env.NEXT_PUBLIC_API_TIMEOUT_MS ?? "12000");
  const deployment = env.NEXT_PUBLIC_DEPLOYMENT_ENV ?? "production";
  if (deployment !== "production" && deployment !== "staging")
    throw new Error("NEXT_PUBLIC_DEPLOYMENT_ENV must be production or staging");
  if (!/^https?:\/\//.test(apiBaseUrl))
    throw new Error("NEXT_PUBLIC_API_BASE_URL must be an absolute HTTP(S) URL");
  if (
    env.NODE_ENV === "production" &&
    env.NEXT_PUBLIC_E2E_ALLOW_MOCK !== "1" &&
    /localhost|127\.0\.0\.1/.test(apiBaseUrl)
  )
    throw new Error("Production requires a non-local NEXT_PUBLIC_API_BASE_URL");
  if (env.NODE_ENV === "production" && mode === "mock" && env.NEXT_PUBLIC_E2E_ALLOW_MOCK !== "1")
    throw new Error("Mock API mode is disabled in production");
  if (env.NODE_ENV === "production" && env.NEXT_PUBLIC_E2E_ALLOW_MOCK !== "1") {
    const requiredOrigin =
      deployment === "staging"
        ? "https://api-staging.breero.com/api/v1"
        : "https://api.breero.com/api/v1";
    if (apiBaseUrl !== requiredOrigin) throw new Error(`${deployment} requires ${requiredOrigin}`);
  }
  if (!Number.isFinite(timeoutMs) || timeoutMs < 1000 || timeoutMs > 60000)
    throw new Error("NEXT_PUBLIC_API_TIMEOUT_MS must be between 1000 and 60000");
  return { apiBaseUrl, mode, timeoutMs };
}

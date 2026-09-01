import type { BreeroApi } from "./client";
import { createBreeroApi } from "./client";
import { readPublicApiConfig } from "./config";
import { createMockBreeroApi, type MockScenario } from "./mock";
import type { AccessTokenProvider } from "./transport";

export function createConfiguredApi(
  env: Record<string, string | undefined>,
  options: {
    getAccessToken?: AccessTokenProvider;
    refreshAccessToken?: () => Promise<string | null>;
    onUnauthorized?: () => void;
    mock?: MockScenario;
  } = {},
): BreeroApi {
  const config = readPublicApiConfig(env);
  return config.mode === "mock"
    ? createMockBreeroApi(options.mock)
    : createBreeroApi({
        baseUrl: config.apiBaseUrl,
        timeoutMs: config.timeoutMs,
        getAccessToken: options.getAccessToken,
        refreshAccessToken: options.refreshAccessToken,
        onUnauthorized: options.onUnauthorized,
      });
}

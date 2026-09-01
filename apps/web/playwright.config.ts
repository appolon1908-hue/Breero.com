import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  outputDir: "./test-results",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://127.0.0.1:3100",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "firefox", use: { ...devices["Desktop Firefox"] } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
  ],
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : {
        command:
          "NEXT_PUBLIC_API_MODE=mock NEXT_PUBLIC_E2E_ALLOW_MOCK=1 pnpm build && NEXT_PUBLIC_API_MODE=mock NEXT_PUBLIC_E2E_ALLOW_MOCK=1 pnpm exec next start -H 127.0.0.1 -p 3100",
        url: "http://127.0.0.1:3100",
        reuseExistingServer: true,
        timeout: 120_000,
      },
});

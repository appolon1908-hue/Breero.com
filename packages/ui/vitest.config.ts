import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    // Floors are ratchets set just under the figures measured on this tree. Raise
    // them as tests land; never lower one to turn a red run green.
    coverage: {
      provider: "v8",
      reporter: ["text-summary"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["**/*.test.{ts,tsx}", "src/index.ts"],
      thresholds: {
        lines: 47,
        statements: 47,
        functions: 27,
        branches: 52,
      },
    },
  },
});

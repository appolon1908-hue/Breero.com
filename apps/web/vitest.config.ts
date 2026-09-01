import { defineConfig } from "vitest/config";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  esbuild: { jsx: "automatic" },
  resolve: { alias: { "@": fileURLToPath(new URL(".", import.meta.url)) } },
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    exclude: ["tests/e2e/**", "node_modules/**", ".next/**"],
    // Floors are ratchets set just under the figures measured on this tree. Raise
    // them as tests land; never lower one to turn a red run green.
    coverage: {
      provider: "v8",
      reporter: ["text-summary"],
      include: ["app/**/*.{ts,tsx}", "components/**/*.{ts,tsx}", "lib/**/*.{ts,tsx}"],
      exclude: ["**/*.test.{ts,tsx}", "app/**/layout.tsx", "app/**/route.ts"],
      thresholds: {
        lines: 17,
        statements: 17,
        functions: 50,
        branches: 57,
      },
    },
  },
});

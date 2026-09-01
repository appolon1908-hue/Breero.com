import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: ["src/**/*.test.ts", "test/**/*.test.ts"],
    // Floors are ratchets set just under the figures measured on this tree. Raise
    // them as tests land; never lower one to turn a red run green.
    coverage: {
      provider: "v8",
      reporter: ["text-summary"],
      include: ["src/**/*.ts"],
      exclude: ["**/*.test.ts", "src/index.ts"],
      thresholds: {
        lines: 59,
        statements: 59,
        functions: 23,
        branches: 70,
      },
    },
  },
});

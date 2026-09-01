import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Without `globals: true`, testing-library does not auto-register cleanup, so each
// render leaks into the next test's document and queries match the wrong tree.
afterEach(cleanup);

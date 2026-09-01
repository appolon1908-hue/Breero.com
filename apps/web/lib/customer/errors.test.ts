import { describe, expect, it } from "vitest";
import { ApiError } from "@breero/api-client";
import { safeCustomerError } from "./errors";

describe("safeCustomerError", () => {
  it("maps API failures to customer-safe messages", () => {
    const raw = new ApiError("database password leaked", "server", 500);
    expect(safeCustomerError(raw).message).toBe(
      "We could not complete that request. Try again shortly.",
    );
  });

  it.each([
    ["validation", 422],
    ["authentication", 401],
    ["forbidden", 403],
    ["not_found", 404],
    ["conflict", 409],
    ["rate_limit", 429],
    ["server", 500],
    ["timeout", undefined],
    ["network", undefined],
  ] as const)("sanitizes %s failures", (kind, status) => {
    const result = safeCustomerError(new ApiError("raw backend detail", kind, status));
    expect(result.message).not.toContain("raw backend detail");
  });

  it("never renders arbitrary exception text", () => {
    expect(safeCustomerError(new Error("raw internal exception")).message).not.toContain(
      "raw internal",
    );
  });
});

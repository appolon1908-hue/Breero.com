import { describe, expect, it, vi } from "vitest";
import { createBreeroApi } from "./client";
import { createConfiguredApi } from "./factory";
import { readPublicApiConfig } from "./config";

describe("BREERO client", () => {
  it("sends idempotency keys on booking writes", async () => {
    const fetcher = vi.fn(async (_url: URL | RequestInfo, init?: RequestInit) => {
      expect(new Headers(init?.headers).get("idempotency-key")).toBe("booking-123456");
      return new Response(JSON.stringify({ id: "b" }), { status: 201 });
    });
    const api = createBreeroApi({
      baseUrl: "https://api.test/api/v1",
      fetch: fetcher as typeof fetch,
    });
    await api.bookings.create(
      {
        service_id: "s",
        address_id: "a",
        customer: { first_name: "A", last_name: "B", email: "a@b.test", phone: "12345" },
        window: { start: "start", end: "end" },
        answers: [],
      },
      "booking-123456",
    );
  });

  it("switches all domains through one mock seam", async () => {
    const api = createConfiguredApi({ NEXT_PUBLIC_API_MODE: "mock" }, { mock: { services: [] } });
    await expect(api.services.list()).resolves.toEqual([]);
  });

  it("accepts the exact live staging origin in a production build", () => {
    expect(
      readPublicApiConfig({
        NODE_ENV: "production",
        NEXT_PUBLIC_DEPLOYMENT_ENV: "staging",
        NEXT_PUBLIC_API_BASE_URL: "https://api-staging.breero.com/api/v1",
        NEXT_PUBLIC_API_MODE: "live",
      }),
    ).toMatchObject({
      apiBaseUrl: "https://api-staging.breero.com/api/v1",
      mode: "live",
    });
  });

  it("rejects a production origin for a staging deployment", () => {
    expect(() =>
      readPublicApiConfig({
        NODE_ENV: "production",
        NEXT_PUBLIC_DEPLOYMENT_ENV: "staging",
        NEXT_PUBLIC_API_BASE_URL: "https://api.breero.com/api/v1",
      }),
    ).toThrow("staging requires https://api-staging.breero.com/api/v1");
  });
});

import { describe, expect, it, vi } from "vitest";
import { ApiError } from "../src/errors";
import { ApiTransport } from "../src/transport";

describe("FetchTransport", () => {
  it("centralizes JSON and bearer authentication", async () => {
    const fetcher = vi.fn(
      async () =>
        new Response(JSON.stringify({ ok: true }), {
          headers: { "content-type": "application/json" },
        }),
    );
    const transport = new ApiTransport({
      baseUrl: "https://api.example.test/api/v1",
      fetch: fetcher as typeof fetch,
      getAccessToken: () => "token",
    });
    await transport.request("/bookings", { method: "POST", body: { service_id: "svc" } });
    expect(fetcher).toHaveBeenCalledOnce();
    const [url, init] = fetcher.mock.calls[0]!;
    expect(url).toBe("https://api.example.test/api/v1/bookings");
    expect(new Headers(init?.headers).get("authorization")).toBe("Bearer token");
    expect(init?.body).toBe(JSON.stringify({ service_id: "svc" }));
  });

  it("normalizes FastAPI validation errors", async () => {
    const response = new Response(
      JSON.stringify({
        detail: [{ loc: ["body", "email"], msg: "invalid email", type: "value_error" }],
      }),
      { status: 422 },
    );
    const transport = new ApiTransport({
      baseUrl: "https://api.example.test",
      fetch: vi.fn(async () => response) as typeof fetch,
    });
    await expect(transport.request("/auth/register")).rejects.toMatchObject<ApiError>({
      kind: "validation",
      status: 422,
    });
  });

  it("does not retry non-idempotent writes", async () => {
    const fetcher = vi.fn(async () => {
      throw new TypeError("offline");
    });
    const transport = new ApiTransport({
      baseUrl: "https://api.example.test",
      fetch: fetcher as typeof fetch,
    });
    await expect(
      transport.request("/bookings", { method: "POST", body: {} }),
    ).rejects.toMatchObject({ kind: "network" });
    expect(fetcher).toHaveBeenCalledOnce();
  });
});

import { describe, expect, it, vi } from "vitest";
import { createBreeroApi } from "../src/client";

describe("API modules", () => {
  it("encodes route identifiers and delegates through one transport", async () => {
    const fetcher = vi.fn(
      async () =>
        new Response(JSON.stringify([]), { headers: { "content-type": "application/json" } }),
    );
    const api = createBreeroApi({
      baseUrl: "https://api.example.test/api/v1",
      fetch: fetcher as typeof fetch,
    });
    await api.services.questions("air/con");
    expect(String(fetcher.mock.calls[0]?.[0])).toBe(
      "https://api.example.test/api/v1/services/air%2Fcon/questions",
    );
  });
});

import { describe, expect, it, vi } from "vitest";
import { isPortalSessionUsable, type PortalSession } from "./index";

const token = (expiresAtSeconds: number) => {
  const payload = Buffer.from(JSON.stringify({ exp: expiresAtSeconds })).toString("base64url");
  return `header.${payload}.signature`;
};

const session = (role: string, expiresAtSeconds: number): PortalSession => ({
  access_token: token(expiresAtSeconds),
  user: {
    email: "operator@breero.com",
    full_name: "BREERO Operator",
    role,
  },
});

describe("isPortalSessionUsable", () => {
  it("accepts an unexpired session for an allowed role", () => {
    vi.setSystemTime(new Date("2026-09-02T20:00:00Z"));
    expect(
      isPortalSessionUsable(session("operations", 1_788_400_000), ["operations", "admin"]),
    ).toBe(true);
    vi.useRealTimers();
  });

  it("rejects an expired session", () => {
    vi.setSystemTime(new Date("2026-09-02T20:00:00Z"));
    expect(
      isPortalSessionUsable(session("operations", 1_700_000_000), ["operations", "admin"]),
    ).toBe(false);
    vi.useRealTimers();
  });

  it("rejects a session whose role is not allowed by the portal", () => {
    expect(
      isPortalSessionUsable(session("vendor_admin", 2_000_000_000), ["finance", "admin"]),
    ).toBe(false);
  });
});

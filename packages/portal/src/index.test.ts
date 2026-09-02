import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
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
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-09-02T20:00:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("accepts an unexpired session for an allowed role", () => {
    expect(
      isPortalSessionUsable(session("operations", 1_788_400_000), ["operations", "admin"]),
    ).toBe(true);
  });

  it("rejects an expired session", () => {
    expect(
      isPortalSessionUsable(session("operations", 1_700_000_000), ["operations", "admin"]),
    ).toBe(false);
  });

  it("rejects a session whose role is not allowed by the portal", () => {
    expect(
      isPortalSessionUsable(session("vendor_admin", 2_000_000_000), ["finance", "admin"]),
    ).toBe(false);
  });
});

import { beforeEach, describe, expect, it, vi } from "vitest";
import { CONSENT_STORAGE_KEY, readConsentChoice, saveConsentChoice } from "./consent";

describe("browser consent storage", () => {
  beforeEach(() => localStorage.clear());
  it("stores analytics and advertising independently", () => {
    saveConsentChoice(true, false, "banner");
    expect(readConsentChoice()).toMatchObject({
      analytics: true,
      advertising: false,
      source: "banner",
    });
  });
  it("migrates analytics-only preferences with advertising denied", () => {
    localStorage.setItem(
      CONSENT_STORAGE_KEY,
      JSON.stringify({ analytics: true, source: "banner" }),
    );
    expect(readConsentChoice()).toMatchObject({ analytics: true, advertising: false });
  });
  it("removes optional identifiers when analytics consent is withdrawn", () => {
    localStorage.setItem("breero_attribution_v1", "campaign");
    localStorage.setItem("breero_anonymous_session_id", "visitor");
    saveConsentChoice(false, false);
    expect(localStorage.getItem("breero_attribution_v1")).toBeNull();
    expect(localStorage.getItem("breero_anonymous_session_id")).toBeNull();
  });
  it("rejects malformed preferences", () => {
    localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify({ analytics: "yes" }));
    expect(readConsentChoice()).toBeNull();
  });
  it("fails closed when browser storage is unavailable", () => {
    const read = vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new DOMException("blocked");
    });
    expect(readConsentChoice()).toBeNull();
    read.mockRestore();
  });
});

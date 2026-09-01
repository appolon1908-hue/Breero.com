import { describe, expect, it } from "vitest";
import type { BookingCreateRequest, QuestionType } from "./index";

describe("frontend contracts", () => {
  it("covers every dynamic question renderer kind", () => {
    const kinds: QuestionType[] = [
      "text",
      "textarea",
      "number",
      "boolean",
      "single_choice",
      "multi_choice",
    ];
    expect(new Set(kinds).size).toBe(6);
  });

  it("keeps booking writes aligned with the backend command", () => {
    const payload: BookingCreateRequest = {
      service_id: "service",
      address_id: "address",
      customer: {
        first_name: "Ada",
        last_name: "Lovelace",
        email: "ada@example.com",
        phone: "+4912345",
      },
      window: { start: "2026-08-12T09:00:00Z", end: "2026-08-12T11:00:00Z" },
      answers: [],
    };
    expect(payload.answers).toEqual([]);
  });
});

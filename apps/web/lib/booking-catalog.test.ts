import { beforeAll, describe, expect, it } from "vitest";
import { bookingApi } from "./booking-api";
import { serviceCatalog } from "./booking-catalog";
beforeAll(() => {
  process.env.NEXT_PUBLIC_API_MODE = "mock";
});
describe("booking catalog adapter", () => {
  it("keeps service slugs and ids unique", () => {
    expect(new Set(serviceCatalog.map((s) => s.slug)).size).toBe(serviceCatalog.length);
    expect(new Set(serviceCatalog.map((s) => s.id)).size).toBe(serviceCatalog.length);
  });
  it("uses backend-supported dynamic question types", () => {
    const kinds = new Set(serviceCatalog.flatMap((s) => s.questions.map((q) => q.question_type)));
    expect(kinds).toEqual(
      new Set(["single_choice", "number", "multi_choice", "textarea", "boolean", "text"]),
    );
  });
});
describe("booking mock failure scenarios", () => {
  it("models service-area rejection without frontend inference", async () => {
    expect(await bookingApi().addresses.validate({ address: "Outside area" })).toMatchObject({
      serviceable: false,
      legal_entity_code: null,
    });
  });
  it("models no availability", async () => {
    expect(
      await bookingApi().availability.search({
        service_id: "handyman",
        address_id: "a",
        date_from: "2026-08-12",
        date_to: "2026-08-20",
      }),
    ).toEqual([]);
  });
  it("models API failure", async () => {
    await expect(bookingApi().addresses.validate({ address: "API failure" })).rejects.toThrow();
  });
  it("models payment failure", async () => {
    await expect(
      bookingApi().payments.createIntent(
        { booking_id: "payment-failure", amount_minor: 100 },
        "key",
      ),
    ).rejects.toThrow();
  });
});

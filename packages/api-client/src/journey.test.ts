import { describe, expect, it } from "vitest";
import { createMockBreeroApi } from "./mock";

describe("mock booking journey", () => {
  it("supports the public funnel through authoritative payment state", async () => {
    const api = createMockBreeroApi({
      services: [
        {
          id: "svc",
          slug: "cleaning",
          name: "Cleaning",
          description: null,
          base_price: "89.00",
          duration_minutes: 120,
          questions: [],
        },
      ],
      address: {
        serviceable: true,
        formatted_address: "1 Main St",
        address_id: "addr",
        service_area_id: "area",
        legal_entity_code: "BREERO_DE",
      },
      slots: [
        { start: "2026-08-12T09:00:00Z", end: "2026-08-12T11:00:00Z", remaining_capacity: 2 },
      ],
      bookings: [
        {
          id: "booking",
          reference: "BR-100",
          status: "PENDING_PAYMENT",
          total_amount: "89.00",
          currency: "EUR",
          window_start: "2026-08-12T09:00:00Z",
          window_end: "2026-08-12T11:00:00Z",
          payment_required: true,
        },
      ],
      bookingCreateResponse: {
        id: "booking",
        reference: "BR-100",
        status: "PENDING_PAYMENT",
        total_amount: "89.00",
        currency: "EUR",
        window_start: "2026-08-12T09:00:00Z",
        window_end: "2026-08-12T11:00:00Z",
        payment_required: true,
        guest_confirmation_token: "test-guest-token",
      },
      payments: [
        {
          id: "payment",
          booking_id: "booking",
          provider: "stripe",
          status: "requires_action",
          amount_minor: 8900,
          currency: "eur",
          captured_amount_minor: 0,
          client_secret: "test-only",
          failure_code: null,
          created_at: "2026-08-11T10:00:00Z",
          updated_at: "2026-08-11T10:00:00Z",
        },
      ],
    });
    const service = (await api.services.list())[0]!;
    const address = await api.addresses.validate({ address: "1 Main St" });
    const slot = (
      await api.availability.search({
        service_id: service.id,
        address_id: address.address_id!,
        date_from: "2026-08-12",
        date_to: "2026-08-12",
      })
    )[0]!;
    const booking = await api.bookings.create(
      {
        service_id: service.id,
        address_id: address.address_id!,
        customer: {
          first_name: "Ada",
          last_name: "Lovelace",
          email: "ada@example.com",
          phone: "+4912345",
        },
        window: slot,
        answers: [],
      },
      "booking-test-100",
    );
    const payment = await api.payments.createIntent(
      { booking_id: booking.id, amount_minor: 8900, currency: "eur" },
      "payment-test-100",
    );
    expect({
      service: service.slug,
      serviceable: address.serviceable,
      booking: booking.status,
      payment: payment.status,
    }).toEqual({
      service: "cleaning",
      serviceable: true,
      booking: "PENDING_PAYMENT",
      payment: "requires_action",
    });
  });
});

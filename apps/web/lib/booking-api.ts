import { createConfiguredApi, type BreeroApi } from "@breero/api-client";
import { createMockBreeroApi } from "@breero/api-client/mock";
import type {
  AddressValidation,
  AvailabilitySlot,
  BookingCreateResponse,
  Payment,
  ServiceDetail,
} from "@breero/types";
import { serviceCatalog } from "./booking-catalog";

const futureSlots = (): AvailabilitySlot[] =>
  Array.from({ length: 6 }, (_, index) => {
    const date = new Date();
    date.setUTCDate(date.getUTCDate() + 1 + Math.floor(index / 2));
    date.setUTCHours(index % 2 ? 13 : 9, 0, 0, 0);
    return {
      start: date.toISOString(),
      end: new Date(date.getTime() + 2 * 60 * 60 * 1000).toISOString(),
      remaining_capacity: (index % 3) + 1,
    };
  });

const mockAddress: AddressValidation = {
  serviceable: true,
  formatted_address: "24 Lindenstraße, Berlin",
  address_id: "address-demo",
  service_area_id: "berlin",
  legal_entity_code: "BREERO-DE",
};
const mockBooking: BookingCreateResponse = {
  id: "booking-demo",
  reference: "BR-240811",
  status: "PENDING_PAYMENT",
  total_amount: "89.00",
  currency: "EUR",
  window_start: futureSlots()[0]!.start,
  window_end: futureSlots()[0]!.end,
  payment_required: true,
  guest_confirmation_token: "mock-guest-confirmation-token-that-is-long-enough",
};
const mockPayment: Payment = {
  id: "payment-demo",
  booking_id: mockBooking.id,
  provider: "mock",
  status: "requires_action",
  amount_minor: 8900,
  currency: "EUR",
  captured_amount_minor: 0,
  client_secret: null,
  failure_code: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

export function bookingApi(): BreeroApi {
  if (process.env.NEXT_PUBLIC_API_MODE !== "mock")
    return createConfiguredApi({
      NODE_ENV: process.env.NODE_ENV,
      NEXT_PUBLIC_API_MODE: process.env.NEXT_PUBLIC_API_MODE,
      NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
      NEXT_PUBLIC_API_TIMEOUT_MS: process.env.NEXT_PUBLIC_API_TIMEOUT_MS,
      NEXT_PUBLIC_E2E_ALLOW_MOCK: process.env.NEXT_PUBLIC_E2E_ALLOW_MOCK,
      NEXT_PUBLIC_DEPLOYMENT_ENV: process.env.NEXT_PUBLIC_DEPLOYMENT_ENV,
    });
  const api = createMockBreeroApi({
    services: serviceCatalog as ServiceDetail[],
    address: mockAddress,
    slots: futureSlots(),
    bookings: [mockBooking],
    bookingCreateResponse: mockBooking,
    payments: [mockPayment],
  });
  return {
    ...api,
    addresses: {
      validate: async (input, signal) => {
        if (signal?.aborted) throw signal.reason;
        if (/api failure/i.test(input.address)) throw new Error("Simulated API failure");
        if (/outside area/i.test(input.address))
          return {
            ...mockAddress,
            serviceable: false,
            address_id: null,
            service_area_id: null,
            legal_entity_code: null,
          };
        return { ...mockAddress, formatted_address: input.address };
      },
    },
    availability: {
      search: async (input, signal) =>
        input.service_id === "handyman" ? [] : api.availability.search(input, signal),
    },
    payments: {
      ...api.payments,
      createIntent: async (input, key, signal) =>
        input.booking_id === "payment-failure"
          ? Promise.reject(new Error("Simulated payment failure"))
          : api.payments.createIntent(input, key, signal),
    },
  };
}

import { analyticsConsentGranted } from "./consent";

export type FunnelEvent =
  | { name: "homepage_viewed" }
  | { name: "service_viewed"; serviceId: string }
  | { name: "booking_started"; serviceId: string }
  | { name: "address_validated"; serviceable: boolean; serviceAreaId?: string }
  | { name: "slot_selected"; serviceId: string; startsAt: string }
  | { name: "booking_submitted"; serviceId: string }
  | { name: "payment_started"; bookingId: string }
  | { name: "backend_confirmed_payment"; bookingId: string }
  | { name: "booking_confirmed"; bookingId: string }
  | { name: "quote_viewed"; quoteId: string }
  | { name: "quote_approved"; quoteId: string };

export interface AnalyticsAdapter {
  track(event: FunnelEvent): void | Promise<void>;
}
const noop: AnalyticsAdapter = { track: () => undefined };
let adapter: AnalyticsAdapter = noop;

export function configureAnalytics(next: AnalyticsAdapter): () => void {
  adapter = next;
  return () => {
    adapter = noop;
  };
}
export function track(event: FunnelEvent): void {
  if (analyticsConsentGranted()) void adapter.track(event);
}

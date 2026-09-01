import type { Booking, CustomerProfile, Payment, Quote } from "@breero/types";

export type CustomerBooking = Booking & {
  service: string; category: string; address: string; professional?: { name: string; company: string; initials: string; rating: number };
  timeline: Array<{ title: string; description?: string; time?: string; status: "complete" | "current" | "upcoming" }>;
};

export const profile: CustomerProfile = { id: "customer-1", email: "maya.thompson@example.com", full_name: "Maya Thompson", phone: "+44 7700 900123", email_verified: true };

export const bookings: CustomerBooking[] = [
  { id: "BR-240817", reference: "BR-240817", status: "CONFIRMED", total_amount: "78.00", currency: "GBP", window_start: "2026-08-17T09:00:00Z", window_end: "2026-08-17T11:00:00Z", payment_required: false, service: "Home cleaning", category: "Cleaning", address: "24 Maple Grove, London, N16 8QJ", professional: { name: "Amara Okafor", company: "Bright Home Co.", initials: "AO", rating: 4.9 }, timeline: [
    { title: "Booking confirmed", time: "11 Aug, 14:32", description: "Payment authorised and your time is reserved.", status: "complete" },
    { title: "Professional assigned", time: "12 Aug, 09:15", description: "Amara from Bright Home Co. will complete your service.", status: "complete" },
    { title: "Service day", time: "17 Aug, 09:00–11:00", description: "We’ll let you know when Amara is on the way.", status: "current" },
    { title: "Service complete", description: "Your receipt will be available here.", status: "upcoming" },
  ] },
  { id: "BR-240802", reference: "BR-240802", status: "PENDING_PROVIDER_CONFIRMATION", total_amount: "45.00", currency: "GBP", window_start: "2026-08-19T13:00:00Z", window_end: "2026-08-19T15:00:00Z", payment_required: true, service: "Kitchen tap repair", category: "Plumbing", address: "24 Maple Grove, London, N16 8QJ", timeline: [
    { title: "Request received", time: "10 Aug, 10:08", status: "complete" }, { title: "Quote ready", time: "11 Aug, 08:40", description: "Review the additional work before 14 August.", status: "current" }, { title: "Service confirmation", status: "upcoming" },
  ] },
  { id: "BR-239104", reference: "BR-239104", status: "CONFIRMED", total_amount: "110.00", currency: "GBP", window_start: "2026-07-28T08:00:00Z", window_end: "2026-07-28T10:00:00Z", payment_required: false, service: "Electrical safety check", category: "Electrical", address: "24 Maple Grove, London, N16 8QJ", professional: { name: "Lewis Grant", company: "Northstar Electrical", initials: "LG", rating: 4.8 }, timeline: [
    { title: "Booking confirmed", time: "24 Jul", status: "complete" }, { title: "Service completed", time: "28 Jul, 09:42", status: "complete" }, { title: "Payment captured", time: "28 Jul, 09:45", status: "complete" },
  ] },
  { id: "BR-237881", reference: "BR-237881", status: "CANCELLED", total_amount: "52.00", currency: "GBP", window_start: "2026-06-05T14:00:00Z", window_end: "2026-06-05T16:00:00Z", payment_required: false, service: "Furniture assembly", category: "Handyman", address: "8 Willow Road, London, E8 3QW", timeline: [{ title: "Booking cancelled", time: "3 Jun", description: "No payment was taken.", status: "complete" }] },
];

export const quotes: Quote[] = [
  { id: "QT-1048", job_id: "JOB-240802", status: "PENDING_CUSTOMER", description: "Replace the worn mixer tap cartridge and test the seals.", currency: "GBP", subtotal_minor: 7700, tax_minor: 850, total_minor: 8550, created_at: "2026-08-11T08:40:00Z", line_items: [
    { description: "Mixer tap cartridge replacement", quantity: 1, unit_price_minor: 4200 },
    { description: "Labour — first hour", quantity: 1, unit_price_minor: 3500 },
  ] },
  { id: "QT-1012", job_id: "JOB-239104", status: "APPROVED", description: "Electrical inspection and written report.", currency: "GBP", subtotal_minor: 11000, tax_minor: 0, total_minor: 11000, created_at: "2026-07-25T12:00:00Z", line_items: [{ description: "Electrical inspection and written report", quantity: 1, unit_price_minor: 11000 }] },
];

export const payments: Payment[] = [
  { id: "PAY-9031", booking_id: "BR-239104", provider: "card", status: "captured", amount_minor: 11000, currency: "GBP", captured_amount_minor: 11000, client_secret: null, failure_code: null, created_at: "2026-07-24T13:12:00Z", updated_at: "2026-07-28T09:45:00Z" },
  { id: "PAY-8990", booking_id: "BR-238771", provider: "card", status: "refunded", amount_minor: 6400, currency: "GBP", captured_amount_minor: 0, client_secret: null, failure_code: null, created_at: "2026-06-18T11:20:00Z", updated_at: "2026-06-20T15:05:00Z" },
  { id: "PAY-8912", booking_id: "BR-237104", provider: "card", status: "captured", amount_minor: 4800, currency: "GBP", captured_amount_minor: 4800, client_secret: null, failure_code: null, created_at: "2026-05-04T16:20:00Z", updated_at: "2026-05-07T12:30:00Z" },
];

export const addresses = [
  { id: "addr-1", label: "Home", line1: "24 Maple Grove", city: "London", postalCode: "N16 8QJ", default: true },
  { id: "addr-2", label: "Mum’s house", line1: "8 Willow Road", city: "London", postalCode: "E8 3QW", default: false },
];

export const formatMoney = (minor: number, currency = "GBP") => new Intl.NumberFormat("en-GB", { style: "currency", currency }).format(minor / 100);
export const formatDate = (value: string, options?: Intl.DateTimeFormatOptions) => new Intl.DateTimeFormat("en-GB", options ?? { day: "numeric", month: "short", year: "numeric" }).format(new Date(value));

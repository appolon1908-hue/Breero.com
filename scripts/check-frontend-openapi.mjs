import { readFileSync } from "node:fs";

const document = JSON.parse(readFileSync(new URL("../apps/api/openapi.json", import.meta.url), "utf8"));
const required = {
  "/api/v2/capabilities": ["get"],
  "/api/v1/public/capabilities": ["get"],
  "/api/v1/auth/login": ["post"],
  "/api/v1/auth/register": ["post"],
  "/api/v1/auth/refresh": ["post"],
  "/api/v1/auth/logout": ["post"],
  "/api/v1/auth/logout-all": ["post"],
  "/api/v1/auth/password/forgot": ["post"],
  "/api/v1/auth/password/reset": ["post"],
  "/api/v1/auth/email/verify": ["post"],
  "/api/v1/services": ["get"],
  "/api/v1/services/{service_id}": ["get"],
  "/api/v1/services/{service_id}/questions": ["get"],
  "/api/v1/service-requests": ["post"],
  "/api/v1/availability/search": ["post"],
  "/api/v1/bookings": ["post"],
  "/api/v1/bookings/{booking_id}/confirmation": ["get"],
  "/api/v1/contact": ["post"],
  "/api/v1/provider-interest": ["post"],
  "/api/v1/privacy-requests": ["post"],
  "/api/v1/communications/preferences": ["post"],
  "/api/v1/customer/profile": ["get", "patch"],
  "/api/v1/customer/addresses": ["get", "post"],
  "/api/v1/customer/addresses/{address_id}": ["patch", "delete"],
  "/api/v1/customer/bookings": ["get"],
  "/api/v1/customer/bookings/{booking_id}": ["get"],
  "/api/v1/customer/bookings/{booking_id}/cancel": ["post"],
  "/api/v1/customer/quotes": ["get"],
  "/api/v1/customer/quotes/{quote_id}": ["get"],
  "/api/v1/customer/quotes/{quote_id}/decision": ["post"],
};

// PR #34 accepted these routes for quote-only, operator-confirmed scheduling.
// Runtime capabilities remain fail-closed; route presence does not enable instant booking.
const forbidden = {
  "/api/v1/bookings/{booking_id}/payment": ["post"],
  "/api/v1/payments/intents": ["post"],
  "/api/v1/payments/webhooks/stripe": ["post"],
};

const missing = [];
for (const [path, methods] of Object.entries(required)) {
  for (const method of methods) if (!document.paths?.[path]?.[method]) missing.push(`${method.toUpperCase()} ${path}`);
}
if (missing.length) {
  console.error(`Frontend API contract is missing:\n${missing.join("\n")}`);
  process.exit(1);
}

const exposed = [];
for (const [path, methods] of Object.entries(forbidden)) {
  for (const method of methods) if (document.paths?.[path]?.[method]) exposed.push(`${method.toUpperCase()} ${path}`);
}
if (exposed.length) {
  console.error(`Payment-disabled API contract exposes forbidden payment routes:\n${exposed.join("\n")}`);
  process.exit(1);
}

const enumExpectations = {
  QuestionType: ["text", "textarea", "number", "boolean", "single_choice", "multi_choice"],
  UserRole: ["customer", "vendor_admin", "technician", "operations", "finance", "admin"],
  BookingStatus: ["PENDING_PAYMENT", "CONFIRMED", "CANCELLED", "EXPIRED"],
  WorkRequestStatus: ["DRAFT", "SUBMITTED", "PENDING_CUSTOMER", "APPROVED_PENDING_PAYMENT", "APPROVED", "DECLINED", "PAID", "CANCELLED", "EXPIRED"],
};
for (const [schema, expected] of Object.entries(enumExpectations)) {
  const actual = document.components?.schemas?.[schema]?.enum ?? [];
  for (const value of expected) if (!actual.includes(value)) missing.push(`${schema}.${value}`);
}
if (missing.length) {
  console.error(`Frontend enum contract is missing:\n${missing.join("\n")}`);
  process.exit(1);
}

console.log(`Payment-disabled manual-scheduling frontend API contract verified: ${Object.keys(required).length} required paths; zero payment mutation routes.`);

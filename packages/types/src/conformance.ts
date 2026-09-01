/**
 * Structural conformance between the hand-written contracts and the API's own schema.
 *
 * `scripts/check-frontend-openapi.mjs` proves the routes exist.
 * `scripts/check-generated-types.mjs` proves `generated.ts` matches `openapi.json`.
 * Neither connects those schemas to the types the web app actually renders, so a
 * backend rename of `window_start` used to ship green and fail in the browser.
 *
 * This file closes that gap with type-level assertions. It emits no runtime code; the
 * check is `tsc --noEmit`, which already runs in the frontend gate.
 *
 * Two distinct things are asserted, and the difference matters:
 *
 *   1. **The field exists on the API schema.** This is the rename guard, and it is
 *      strict. A field the API does not have is a build failure.
 *
 *   2. **The types are compatible in at least one direction.** Deliberately not
 *      strict assignability. `Booking.status` is `string` here while the API emits a
 *      closed union of eight states: that is the hand-written type being *wider* than
 *      reality, which is safe at runtime and is a modelling choice, not drift. What
 *      this does catch is a genuine conflict — `string` where the API sends a number,
 *      or an object where it sends an array.
 */

import type { components } from "./generated";
import type {
  AvailabilitySlot,
  Booking,
  BookingConfirmation,
  CustomerAddress,
  CustomerProfile,
  LoginRequest,
  MessageResponse,
  ServiceQuestion,
  ServiceSummary,
} from "./index";

type Schemas = components["schemas"];

/** True when either side is assignable to the other. Permits widening and narrowing. */
type Compatible<A, B> = [A] extends [B] ? true : [B] extends [A] ? true : false;

type ConformsTo<Hand, Schema> = {
  [K in keyof Hand]-?: K extends keyof Schema
    ? Compatible<NonNullable<Hand[K]>, NonNullable<Schema[K]>> extends true
      ? true
      : ["incompatible type for", K, Hand[K], "versus", Schema[K]]
    : ["field absent from the API schema:", K];
};

type AllTrue<T> = T[keyof T] extends true ? true : T;

/** Fails compilation with a tuple naming the offending field. */
type Assert<T extends true> = T;

// ---------------------------------------------------------------------------
// Booking — read directly by the account screens.
// ---------------------------------------------------------------------------

type _Booking = Assert<
  AllTrue<
    ConformsTo<
      Pick<
        Booking,
        | "id"
        | "reference"
        | "status"
        | "total_amount"
        | "currency"
        | "window_start"
        | "window_end"
        | "payment_required"
      >,
      Schemas["BookingResponse"]
    >
  >
>;

type _BookingConfirmation = Assert<
  AllTrue<
    ConformsTo<
      Pick<
        BookingConfirmation,
        | "booking_id"
        | "reference"
        | "booking_status"
        | "payment_status"
        | "window_start"
        | "window_end"
        | "amount_minor"
        | "currency"
      >,
      Schemas["BookingConfirmation"]
    >
  >
>;

// ---------------------------------------------------------------------------
// Catalog — rendered on every service page.
// ---------------------------------------------------------------------------

type _ServiceSummary = Assert<
  AllTrue<
    ConformsTo<Pick<ServiceSummary, "id" | "slug" | "name" | "description">, Schemas["ServiceRead"]>
  >
>;

type _ServiceQuestion = Assert<
  AllTrue<
    ConformsTo<
      Pick<ServiceQuestion, "id" | "key" | "label" | "required" | "sort_order" | "help_text">,
      Schemas["QuestionRead"]
    >
  >
>;

type _AvailabilitySlot = Assert<
  AllTrue<ConformsTo<Pick<AvailabilitySlot, "start" | "end">, Schemas["AvailabilitySlot"]>>
>;

// ---------------------------------------------------------------------------
// Customer account.
// ---------------------------------------------------------------------------

type _CustomerProfile = Assert<
  AllTrue<ConformsTo<Pick<CustomerProfile, "email" | "full_name">, Schemas["ProfileRead"]>>
>;

type _CustomerAddress = Assert<
  AllTrue<
    ConformsTo<
      Pick<CustomerAddress, "id" | "line1" | "city" | "postal_code">,
      Schemas["AddressRead"]
    >
  >
>;

// ---------------------------------------------------------------------------
// Auth.
// ---------------------------------------------------------------------------

type _LoginRequest = Assert<
  AllTrue<ConformsTo<Pick<LoginRequest, "email" | "password">, Schemas["LoginRequest"]>>
>;

type _MessageResponse = Assert<
  AllTrue<ConformsTo<Pick<MessageResponse, "message">, Schemas["MessageResponse"]>>
>;

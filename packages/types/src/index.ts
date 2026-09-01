import type { components } from "./generated/openapi";

export type { components, operations, paths } from "./generated/openapi";
export type * from "./feature-gated";
export type * from "./scalars";

type Schemas = components["schemas"];

// Public release contract. Every alias below is generated from apps/api/openapi.json.
export type PublicCapabilities = Schemas["PublicCapabilities"];

export type QuestionType = Schemas["QuestionType"];
export type QuestionOption = Schemas["QuestionOption"];
export type ServiceQuestion = Schemas["QuestionRead"];
export type ServiceSummary = Schemas["ServiceRead"];
export type ServiceDetail = Schemas["ServiceDetail"];

export type AvailabilitySearchRequest = Schemas["AvailabilitySearchRequest"];
export type AvailabilitySlot = Schemas["AvailabilitySlot"];

export type CustomerInput = Schemas["CustomerInput"];
export type BookingAnswerInput = Schemas["BookingAnswerInput"];
export type BookingWindow = Schemas["BookingWindow"];
export type BookingCreateRequest = Schemas["BookingCreateRequest"];
export type BookingStatus = Schemas["BookingStatus"];
export type Booking = Schemas["BookingResponse"];
export type BookingCreateResponse = Schemas["BookingCreateResponse"];
export type BookingConfirmation = Schemas["BookingConfirmation"];
export type CustomerBookingList = Schemas["Page_BookingResponse_"];

export type UserRole = Schemas["UserRole"];
export type User = Schemas["UserRead"];
export type LoginRequest = Schemas["LoginRequest"];
export type RegisterRequest = Schemas["RegisterRequest"];
export type AuthSession = Schemas["TokenResponse"];
export type RefreshRequest = Schemas["RefreshRequest"];
export type MessageResponse = Schemas["MessageResponse"];
export type ForgotPasswordRequest = Schemas["ForgotPasswordRequest"];
export type ResetPasswordRequest = Schemas["ResetPasswordRequest"];
export type ChangePasswordRequest = Schemas["ChangePasswordRequest"];
export type TokenRequest = Schemas["TokenRequest"];

export type CustomerProfile = Schemas["ProfileRead"];
export type CustomerProfilePatch = Schemas["ProfilePatch"];
export type CustomerAddress = Schemas["AddressRead"];
export type CustomerAddressInput = Schemas["AddressInput"];

export type WorkLineItem = Schemas["WorkLineItem"];
export type QuoteStatus = Schemas["WorkRequestStatus"];
export type Quote = Schemas["WorkRequestRead"];
export type QuoteList = Schemas["Page_WorkRequestRead_"];

/** Generic convenience view whose pagination metadata remains OpenAPI-owned. */
export type Page<T> = Omit<CustomerBookingList, "items"> & { items: T[] };

import type { ISODateTime, UUID } from "./scalars";

/**
 * Contracts in this file are deliberately outside the payment-disabled release
 * OpenAPI document. They remain isolated so generated release types cannot be
 * mistaken for future or capability-gated APIs.
 */
export interface AddressValidationRequest {
  address: string;
  line1?: string | null;
  city?: string | null;
  state_code?: string | null;
  postal_code?: string | null;
  country_code?: string;
  latitude?: number | null;
  longitude?: number | null;
}

export interface AddressValidation {
  serviceable: boolean;
  formatted_address: string;
  address_id: UUID | null;
  service_area_id: UUID | null;
  legal_entity_code: string | null;
}

export type PaymentStatus =
  | "created"
  | "requires_action"
  | "authorized"
  | "captured"
  | "failed"
  | "canceled"
  | "refunded"
  | "partially_refunded";

export type PaymentPurpose =
  | "BOOKING_DIAGNOSTIC"
  | "QUOTE_ADDITIONAL_WORK"
  | "PROFESSIONAL_LEAD";

export interface PaymentIntentRequest {
  booking_id?: UUID | null;
  quote_id?: UUID | null;
  lead_purchase_id?: UUID | null;
  payment_purpose?: PaymentPurpose;
  amount_minor: number;
  currency: string;
  capture_method?: "automatic" | "manual";
  metadata?: Record<string, string>;
}

export interface Payment {
  id: UUID;
  booking_id: UUID | null;
  quote_id?: UUID | null;
  lead_purchase_id?: UUID | null;
  payment_purpose?: PaymentPurpose;
  provider: string;
  status: PaymentStatus;
  amount_minor: number;
  currency: string;
  captured_amount_minor: number;
  client_secret?: string | null;
  failure_code: string | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export interface CustomerPayment {
  id: UUID;
  booking_id: UUID | null;
  quote_id: UUID | null;
  payment_purpose: PaymentPurpose;
  provider: string;
  status: PaymentStatus;
  amount_minor: number;
  currency: string;
  captured_amount_minor: number;
  refunded_amount_minor: number;
  failure_code: string | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

export type CustomerPaymentList = {
  items: CustomerPayment[];
  total: number;
  page: number;
  page_size: number;
};

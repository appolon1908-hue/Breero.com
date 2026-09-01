import type { PortalCapabilities } from "@breero/portal";

export type StatusCount = { status: string; count: number };
export type MoneyStatus = { status: string; currency: string; count: number; amount_minor: number };
export type Capabilities = PortalCapabilities;
export type ListResponse<T> = { items: T[]; total: number };

export type AuditEvent = {
  id: string;
  actor_id: string | null;
  actor_type: string;
  action: string;
  resource_type: string;
  resource_id: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type AdminOverview = {
  capabilities: Capabilities;
  users_total: number;
  users_active: number;
  customers_total: number;
  service_zones_total: number;
  service_zones_active: number;
  postal_codes_total: number;
  postal_codes_active: number;
  bookings: StatusCount[];
  jobs: StatusCount[];
  vendors: StatusCount[];
  provider_applications: StatusCount[];
  earnings: MoneyStatus[];
  payout_batches: StatusCount[];
  outbox: StatusCount[];
  recent_audit: AuditEvent[];
};

export type User = {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  email_verified: boolean;
  created_at: string;
};

export type AccessAssignment = {
  role: string;
  department: string;
  tenant_scope: string;
  vendor_id: string | null;
  is_primary: boolean;
};

export type AccessContext = {
  user: User;
  brand_key: string;
  dashboard_path: string;
  roles: string[];
  departments: string[];
  permissions: string[];
  assignments: AccessAssignment[];
  identity_mode: string;
};

export type AccessCatalog = {
  roles: string[];
  departments: string[];
  tenant_scopes: string[];
};

export type ServiceZone = {
  id: string;
  name: string;
  country_code: string;
  timezone_name: string;
  active: boolean;
  boundary: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type PostalCode = {
  id: string;
  service_zone_id: string;
  country_code: string;
  postal_code: string;
  city: string | null;
  state_region: string | null;
  timezone_name: string;
  active: boolean;
  created_at: string;
  updated_at: string;
};

export type Vendor = {
  id: string;
  display_name: string;
  legal_name: string;
  status: string;
};

export type CompensationPlan = {
  id: string;
  vendor_id: string;
  name: string;
  method: string;
  fixed_minor: number | null;
  percentage_bps: number | null;
  currency: string;
  hold_days: number;
  active: boolean;
  effective_from: string;
  effective_to: string | null;
  created_at: string;
  updated_at: string;
};

export type Earning = {
  id: string;
  vendor_id: string;
  job_id: string;
  gross_minor: number;
  fee_minor: number;
  net_minor: number;
  adjustment_total_minor: number;
  payable_minor: number;
  currency: string;
  status: string;
  available_at: string;
  payout_batch_id: string | null;
  created_at: string;
};

export type PayoutBatch = {
  id: string;
  reference: string;
  status: string;
  currency: string;
  total_minor: number;
  earning_count: number;
  reviewed_by: string | null;
  reviewed_at: string | null;
  approved_by: string | null;
  approved_at: string | null;
  submitted_at: string | null;
  provider_status: string | null;
  failure_reason: string | null;
  created_at: string;
};

export type IntegrationConfig = {
  middleware_enabled: boolean;
  middleware_url_configured: boolean;
  middleware_api_key_configured: boolean;
  middleware_webhook_secret_configured: boolean;
  odoo_enabled: boolean;
  odoo_url_configured: boolean;
  odoo_api_key_configured: boolean;
};

export type IntegrationOperation = {
  id: string;
  operation_type: string;
  actor_id: string | null;
  before_counts: Record<string, number>;
  after_counts: Record<string, number>;
  affected_count: number;
  created_at: string;
};

export function total(rows: StatusCount[], values?: readonly string[]): number {
  const accepted = values ? new Set(values.map((value) => value.toUpperCase())) : null;
  return rows.reduce(
    (sum, row) => sum + (!accepted || accepted.has(row.status.toUpperCase()) ? row.count : 0),
    0,
  );
}

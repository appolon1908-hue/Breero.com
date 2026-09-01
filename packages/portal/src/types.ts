import type { ReactNode } from "react";

export type PortalRole =
  | "vendor_admin"
  | "technician"
  | "operations"
  | "finance"
  | "admin"
  | "superadmin"
  | "ops_manager"
  | "support";

export type Row = Record<string, unknown>;

export interface PortalColumn {
  key: string;
  label: string;
  /** Render a cell. Falls back to a readable scalar when omitted. */
  render?: (row: Row) => ReactNode;
  /** Right-align numeric columns so digits line up. */
  numeric?: boolean;
}

export interface PortalAction {
  label: string;
  method: "POST" | "PATCH" | "PUT" | "DELETE";
  path: (row: Row) => string;
  body?: (row: Row) => unknown;
  /**
   * Shown before the request is sent. Required for anything a person cannot undo
   * from this screen — approving a provider, rejecting an application, cancelling.
   */
  confirm?: string;
  /** Hide the action for rows it cannot apply to, rather than failing server-side. */
  available?: (row: Row) => boolean;
  /** Marks an action as destructive so it is styled and confirmed as one. */
  destructive?: boolean;
}

export interface PortalSection {
  slug: string;
  label: string;
  description: string;
  /**
   * The API path this section reads. When absent the section is *blocked*: the
   * capability has no canonical endpoint yet, and the portal says so instead of
   * rendering an empty table that looks like "no records".
   */
  source?: string;
  /** Why the section is blocked. Required when `source` is absent. */
  blockedReason?: string;
  /** What would unblock it, so the note is actionable rather than an apology. */
  blockedOn?: string;
  columns?: PortalColumn[];
  actions?: PortalAction[];
  /** Empty-state copy, so an empty queue reads differently from a missing feature. */
  emptyTitle?: string;
  emptyDescription?: string;
}

export interface PortalConfig {
  name: string;
  eyebrow: string;
  /** Roles permitted to sign in. Enforced again by the API on every request. */
  allowedRoles: PortalRole[];
  sections: PortalSection[];
}

export interface PortalUser {
  email: string;
  full_name: string;
  role: string;
}

export interface PortalSession {
  access_token: string;
  refresh_token?: string;
  user: PortalUser;
}

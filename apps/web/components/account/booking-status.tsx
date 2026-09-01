import type { BookingStatus as BookingStatusValue } from "@breero/types";
import { StatusBadge } from "@breero/ui";

const map = {
  REQUESTED: "pending",
  PENDING_MANUAL_DISPATCH: "pending",
  TENTATIVE_HOLD: "pending",
  PENDING_PAYMENT: "pending",
  PENDING_PROVIDER_CONFIRMATION: "pending",
  CONFIRMED: "confirmed",
  CANCELLED: "cancelled",
  EXPIRED: "cancelled",
} as const satisfies Record<BookingStatusValue, "pending" | "confirmed" | "cancelled">;

export function BookingStatus({ status }: { status: BookingStatusValue }) {
  return <StatusBadge status={map[status]}>{status.replaceAll("_", " ").toLowerCase()}</StatusBadge>;
}

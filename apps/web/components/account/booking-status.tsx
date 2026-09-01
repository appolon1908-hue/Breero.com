import { StatusBadge } from "@breero/ui";

const map = {
  CONFIRMED: "confirmed",
  AWAITING_QUOTE: "pending",
  COMPLETED: "completed",
  CANCELLED: "cancelled",
  IN_PROGRESS: "in-progress",
} as const;
export function BookingStatus({ status }: { status: string }) {
  const variant = map[status as keyof typeof map] ?? "pending";
  return (
    <StatusBadge status={variant}>
      {status === "AWAITING_QUOTE" ? "Quote ready" : status.replaceAll("_", " ").toLowerCase()}
    </StatusBadge>
  );
}

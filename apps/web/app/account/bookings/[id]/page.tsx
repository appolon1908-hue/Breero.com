"use client";

import { useCallback, useState } from "react";
import { useParams } from "next/navigation";
import {
  CalendarIcon,
  Card,
  ClockIcon,
  ErrorState,
  LoadingState,
  Price,
  ShieldIcon,
  StatusBadge,
} from "@breero/ui";
import { customerApi } from "@/lib/customer/api";
import { useApiResource } from "@/lib/customer/use-api-resource";

export default function BookingDetail() {
  const id = String(useParams<{ id: string }>().id);
  const [cancelState, setCancelState] = useState<"idle" | "busy" | "done" | "error">("idle");
  const load = useCallback((signal: AbortSignal) => customerApi.bookings.getMine(id, signal), [id]);
  const { value: booking, error, retry } = useApiResource(load);
  if (error)
    return <ErrorState title="Booking not available" description={error.message} onRetry={retry} />;
  if (!booking) return <LoadingState label="Loading booking details" />;
  const status = booking.status.toLowerCase().replaceAll("_", "-") as
    | "pending"
    | "confirmed"
    | "in-progress"
    | "completed"
    | "cancelled";
  async function cancelBooking() {
    setCancelState("busy");
    try {
      await customerApi.bookings.cancelMine(id);
      setCancelState("done");
      retry();
    } catch {
      setCancelState("error");
    }
  }
  return (
    <>
      <a className="account-back" href="/account/bookings">
        ← Back to bookings
      </a>
      <div className="detail-hero">
        <div>
          <StatusBadge status={status} />
          <h1>BREERO home service</h1>
          <p>Booking {booking.reference}</p>
        </div>
        <div className="detail-hero__amount">
          <small>{booking.payment_required ? "Payment required" : "Booking total"}</small>
          <Price amount={Number(booking.total_amount)} currency={booking.currency} />
        </div>
      </div>
      <div className="account-grid">
        <Card className="account-col-7 detail-section">
          <h2>Booking details</h2>
          <div className="detail-list">
            <div className="detail-row">
              <CalendarIcon />
              <div>
                <small>Date</small>
                <strong>
                  {new Date(booking.window_start).toLocaleDateString("en-GB", {
                    dateStyle: "full",
                  })}
                </strong>
              </div>
            </div>
            <div className="detail-row">
              <ClockIcon />
              <div>
                <small>Arrival window</small>
                <strong>
                  {new Date(booking.window_start).toLocaleTimeString("en-GB", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                  –
                  {new Date(booking.window_end).toLocaleTimeString("en-GB", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </strong>
              </div>
            </div>
          </div>
        </Card>
        <Card className="account-col-5 detail-section">
          <h2>Next steps</h2>
          <p>
            {booking.payment_required
              ? "Complete the secure payment step to reserve this appointment. Confirmation is based on the authoritative payment status."
              : "Your booking is in our system. We’ll show further assignment and arrival details when they become available."}
          </p>
          <div className="support-path">
            <strong>Need help?</strong>
            <span>Our support team can help with changes or concerns.</span>
            <a href="/help">Contact BREERO support →</a>
          </div>
          {!terminalBooking(booking.status) && (
            <div className="detail-actions">
              <button
                className="br-button br-button--outline br-button--md"
                type="button"
                disabled={cancelState === "busy"}
                onClick={cancelBooking}
              >
                {cancelState === "busy" ? "Cancelling…" : "Cancel booking"}
              </button>
              {cancelState === "done" && (
                <p role="status">
                  Cancellation recorded. Any refund status shown by BREERO comes from the backend
                  and may take time.
                </p>
              )}
              {cancelState === "error" && (
                <p className="auth-message auth-error" role="alert">
                  Cancellation could not be completed. No refund has been assumed.
                </p>
              )}
            </div>
          )}
        </Card>
        <Card className="account-col-12 detail-section">
          <h2>Payment summary</h2>
          <Price amount={Number(booking.total_amount)} currency={booking.currency} />
          <p className="safe-payment-note">
            <ShieldIcon size={18} />
            Provider secrets, internal pricing, and professional compensation are never exposed.
          </p>
        </Card>
      </div>
    </>
  );
}

function terminalBooking(status: string) {
  return ["COMPLETED", "CANCELLED", "EXPIRED"].includes(status);
}

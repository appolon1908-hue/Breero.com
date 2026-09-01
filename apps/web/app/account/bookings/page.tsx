"use client";

import { useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { Button, Card, EmptyState, ErrorState, LoadingState, Price, StatusBadge } from "@breero/ui";
import type { Booking } from "@breero/types";
import { AccountPageHeader } from "@/components/account/page-header";
import { customerApi } from "@/lib/customer/api";
import { useApiResource } from "@/lib/customer/use-api-resource";

const terminal = new Set(["COMPLETED", "CANCELLED"]);
export default function BookingsPage() {
  const view = useSearchParams().get("view") ?? "active";
  const load = useCallback(async (signal: AbortSignal) => {
    const result = await customerApi.bookings.mine(undefined, signal);
    return result.items;
  }, []);
  const { value, error, retry } = useApiResource<Booking[]>(load);
  const shown = value?.filter(
    (booking) =>
      view === "all" ||
      (view === "history" ? terminal.has(booking.status) : !terminal.has(booking.status)),
  );
  return (
    <>
      <AccountPageHeader
        eyebrow="Your services"
        title="Bookings"
        description="Track upcoming visits and revisit everything we’ve handled."
        action={
          <a className="br-button br-button--primary br-button--sm" href="/services">
            Book something new
          </a>
        }
      />
      <nav className="booking-filters" aria-label="Filter bookings">
        <a
          href="/account/bookings?view=active"
          aria-current={view === "active" ? "page" : undefined}
        >
          Active
        </a>
        <a
          href="/account/bookings?view=history"
          aria-current={view === "history" ? "page" : undefined}
        >
          History
        </a>
        <a href="/account/bookings?view=all" aria-current={view === "all" ? "page" : undefined}>
          All bookings
        </a>
      </nav>
      {error ? (
        <ErrorState title="Bookings aren’t available" description={error.message} onRetry={retry} />
      ) : !shown ? (
        <LoadingState label="Loading your bookings" />
      ) : shown.length ? (
        <div className="booking-list">
          {shown.map((booking) => (
            <a
              className="booking-card-link"
              href={`/account/bookings/${booking.id}`}
              key={booking.id}
            >
              <Card interactive className="booking-card">
                <div className="booking-card__top">
                  <div>
                    <small>{booking.reference}</small>
                    <h2>BREERO home service</h2>
                  </div>
                  <StatusBadge
                    status={
                      booking.status.toLowerCase().replaceAll("_", "-") as
                        | "pending"
                        | "confirmed"
                        | "in-progress"
                        | "completed"
                        | "cancelled"
                    }
                  />
                </div>
                <div className="booking-card__meta">
                  <span>
                    {new Date(booking.window_start).toLocaleDateString("en-GB", {
                      dateStyle: "medium",
                    })}
                  </span>
                  <span>
                    {new Date(booking.window_start).toLocaleTimeString("en-GB", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                    –
                    {new Date(booking.window_end).toLocaleTimeString("en-GB", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                  <Price amount={Number(booking.total_amount)} currency={booking.currency} />
                </div>
              </Card>
            </a>
          ))}
        </div>
      ) : (
        <EmptyState
          title="No bookings here yet"
          description="When you book a service, you’ll be able to track it here."
          action={
            <Button onClick={() => window.location.assign("/services")}>Explore services</Button>
          }
        />
      )}
    </>
  );
}

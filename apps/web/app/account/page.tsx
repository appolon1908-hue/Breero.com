"use client";

import { useCallback } from "react";
import {
  ArrowRightIcon,
  Badge,
  CalendarIcon,
  Card,
  EmptyState,
  ErrorState,
  HomeIcon,
  LoadingState,
  Price,
  ShieldIcon,
} from "@breero/ui";
import type { Booking, CustomerPayment, CustomerProfile, Quote } from "@breero/types";
import { AccountPageHeader } from "@/components/account/page-header";
import { customerApi } from "@/lib/customer/api";
import { useApiResource } from "@/lib/customer/use-api-resource";

type DashboardData = {
  profile: CustomerProfile;
  bookings: Booking[];
  quotes: Quote[];
  payments: CustomerPayment[];
};
export default function AccountDashboard() {
  const load = useCallback(async (signal: AbortSignal): Promise<DashboardData> => {
    const [profile, bookings, quotes] = await Promise.all([
      customerApi.customer.profile(signal),
      customerApi.bookings.mine(undefined, signal),
      customerApi.quotes.list(undefined, signal),
    ]);
    return { profile, bookings: bookings.items, quotes: quotes.items, payments: [] };
  }, []);
  const { value, error, retry } = useApiResource(load);
  if (error)
    return (
      <ErrorState
        title="We couldn’t load your account"
        description={error.message}
        onRetry={retry}
      />
    );
  if (!value) return <LoadingState label="Loading your account" />;
  const upcoming = value.bookings.find(
    (booking) => !["COMPLETED", "CANCELLED"].includes(booking.status),
  );
  const pendingQuote = value.quotes.find((quote) => quote.status === "PENDING");
  const paid = value.payments.reduce((sum, payment) => sum + payment.captured_amount_minor, 0);
  return (
    <>
      <AccountPageHeader
        eyebrow="Welcome back"
        title={`Hello, ${value.profile.full_name.split(" ")[0]}`}
        description="Here’s what’s happening with your home."
        action={
          <a className="br-button br-button--primary br-button--sm" href="/services">
            Book a service
          </a>
        }
      />
      <div className="account-grid">
        {upcoming ? (
          <Card className="account-col-7 upcoming-card">
            <div className="account-card-title">
              <h2>Next booking</h2>
              <a href={`/account/bookings/${upcoming.id}`}>
                View details <ArrowRightIcon size={15} />
              </a>
            </div>
            <div className="upcoming-card__date">
              <span>
                <small>
                  {new Date(upcoming.window_start)
                    .toLocaleDateString("en-GB", { month: "short" })
                    .toUpperCase()}
                </small>
                <strong>{new Date(upcoming.window_start).getDate()}</strong>
              </span>
              <div>
                <h3>BREERO home service</h3>
                <p>
                  {new Date(upcoming.window_start).toLocaleTimeString("en-GB", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                  –
                  {new Date(upcoming.window_end).toLocaleTimeString("en-GB", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
            </div>
          </Card>
        ) : (
          <Card className="account-col-7">
            <EmptyState
              title="No upcoming bookings"
              description="Choose a service whenever your home needs a hand."
            />
          </Card>
        )}
        {pendingQuote ? (
          <Card className="account-col-5 quote-callout">
            <div>
              <Badge variant="warning">Action needed</Badge>
            </div>
            <h2>Additional work needs your approval</h2>
            <p>{pendingQuote.description}</p>
            <div className="quote-callout__bottom">
              <Price amount={pendingQuote.total_minor / 100} currency={pendingQuote.currency} />
              <a
                className="br-button br-button--primary br-button--sm"
                href={`/account/quotes/${pendingQuote.id}`}
              >
                Review quote
              </a>
            </div>
          </Card>
        ) : (
          <Card className="account-col-5">
            <EmptyState
              title="No quotes awaiting review"
              description="We’ll notify you before any additional work begins."
            />
          </Card>
        )}
        <Card className="account-col-4 metric-card">
          <span>
            <CalendarIcon />
          </span>
          <strong>
            {value.bookings.filter((booking) => booking.status === "COMPLETED").length}
          </strong>
          <p>Completed services</p>
        </Card>
        <Card className="account-col-4 metric-card">
          <span>
            <ShieldIcon />
          </span>
          <strong>
            {new Intl.NumberFormat("en-GB", {
              style: "currency",
              currency: value.payments[0]?.currency ?? "EUR",
            }).format(paid / 100)}
          </strong>
          <p>Captured securely</p>
        </Card>
        <Card className="account-col-4 metric-card">
          <span>
            <HomeIcon />
          </span>
          <strong>{value.bookings.length}</strong>
          <p>Total bookings</p>
        </Card>
        <Card className="account-col-12">
          <div className="account-card-title">
            <h2>Quick actions</h2>
          </div>
          <div className="quick-actions">
            <a href="/services">
              <CalendarIcon />
              Book a service
            </a>
            <a href="/account/addresses">
              <HomeIcon />
              Addresses
            </a>
            <a href="/help">
              <ShieldIcon />
              Get support
            </a>
          </div>
        </Card>
      </div>
    </>
  );
}

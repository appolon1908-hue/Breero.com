"use client";
import { ErrorState } from "@breero/ui";
export default function AccountError({ reset }: { error: Error; reset: () => void }) {
  return (
    <ErrorState
      title="We couldn’t load your account"
      description="Your bookings are safe. Check your connection and try again."
      onRetry={reset}
    />
  );
}

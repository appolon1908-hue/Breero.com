"use client";
import { ErrorState } from "@breero/ui";
export default function Error({ reset }: { error: Error; reset: () => void }) {
  return (
    <ErrorState
      title="Quotes aren’t available"
      description="Nothing has been approved or charged. Try loading your quotes again."
      onRetry={reset}
    />
  );
}

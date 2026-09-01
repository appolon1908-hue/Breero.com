"use client";

import { useState } from "react";
import { Button, CheckIcon } from "@breero/ui";
import { customerApi } from "@/lib/customer/api";

export function QuoteApproval({
  quoteId,
}: {
  quoteId: string;
  amountMinor: number;
  currency: string;
}) {
  const [state, setState] = useState<
    "idle" | "approving" | "declining" | "approved" | "declined" | "error"
  >("idle");
  async function approve() {
    setState("approving");
    try {
      await customerApi.quotes.decide(quoteId, true);
      setState("approved");
    } catch {
      setState("error");
    }
  }
  async function decline() {
    setState("declining");
    try {
      await customerApi.quotes.decide(quoteId, false);
      setState("declined");
    } catch {
      setState("error");
    }
  }
  if (state === "declined")
    return (
      <div className="approval-success" role="status">
        <span>
          <CheckIcon size={28} />
        </span>
        <h2>Quote declined</h2>
        <p>Your decision is saved. No additional work or payment was authorized.</p>
        <a href="/account/quotes">Return to quotes</a>
      </div>
    );
  if (state === "approved")
    return (
      <div className="approval-success" role="status">
        <span>
          <CheckIcon size={28} />
        </span>
        <h2>Quote response saved</h2>
        <p>
          Your response is recorded. BREERO does not collect online payment. Final scope, price, and
          payment arrangements remain between you and the independent provider.
        </p>
        <a href="/account/quotes">Return to quotes</a>
      </div>
    );
  return (
    <div>
      <h2>Approve this work?</h2>
      <p>No additional work begins until you approve. Approval does not create an online charge.</p>
      {state === "error" && (
        <p className="auth-message auth-error" role="alert">
          We couldn’t complete that request. Nothing was charged.
        </p>
      )}
      <Button fullWidth loading={state === "approving"} onClick={approve}>
        Approve quote
      </Button>
      <Button fullWidth variant="outline" loading={state === "declining"} onClick={decline}>
        Decline quote
      </Button>
    </div>
  );
}

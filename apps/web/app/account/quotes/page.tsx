"use client";

import { useCallback } from "react";
import { Badge, Card, EmptyState, ErrorState, LoadingState, Price } from "@breero/ui";
import type { Quote } from "@breero/types";
import { AccountPageHeader } from "@/components/account/page-header";
import { customerApi } from "@/lib/customer/api";
import { useApiResource } from "@/lib/customer/use-api-resource";

const quoteVariant = (status: Quote["status"]) => status === "PENDING_CUSTOMER" ? "warning" : status === "APPROVED" || status === "PAID" ? "success" : "neutral";

export default function QuotesPage() {
  const load = useCallback(async (signal: AbortSignal) => (await customerApi.quotes.list(undefined, signal)).items, []);
  const { value: quotes, error, retry } = useApiResource<Quote[]>(load);
  return <><AccountPageHeader eyebrow="Review & decide" title="Quotes" description="Clear costs and terms before any additional work begins."/>{error ? <ErrorState title="Quotes aren’t available" description={error.message} onRetry={retry}/> : !quotes ? <LoadingState label="Loading your quotes"/> : quotes.length ? <div className="quote-list">{quotes.map((quote) => <a className="booking-card-link" href={`/account/quotes/${quote.id}`} key={quote.id}><Card interactive className="quote-item"><div><Badge variant={quoteVariant(quote.status)}>{quote.status.replaceAll("_", " ")}</Badge><h2>Additional work request</h2><p>{quote.description} · {new Date(quote.created_at).toLocaleDateString("en-GB", { dateStyle: "medium" })}</p></div><div className="quote-item__side"><Price amount={quote.total_minor / 100} currency={quote.currency}/><strong>View quote →</strong></div></Card></a>)}</div> : <EmptyState title="No quotes to review" description="If a professional recommends additional work, their quote will appear here before anything changes."/>}</>;
}

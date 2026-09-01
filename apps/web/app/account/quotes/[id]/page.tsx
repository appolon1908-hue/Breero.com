"use client";

import { useCallback } from "react";
import { useParams } from "next/navigation";
import { Badge, Card, ErrorState, LoadingState, Price } from "@breero/ui";
import type { Quote } from "@breero/types";
import { QuoteApproval } from "@/components/account/quote-approval";
import { customerApi } from "@/lib/customer/api";
import { useApiResource } from "@/lib/customer/use-api-resource";

const quoteVariant = (status: Quote["status"]) => status === "PENDING_CUSTOMER" ? "warning" : status === "APPROVED" || status === "PAID" ? "success" : "neutral";

export default function QuoteDetail() {
  const id = String(useParams<{ id: string }>().id);
  const load = useCallback((signal: AbortSignal) => customerApi.quotes.get(id, signal), [id]);
  const { value: quote, error, retry } = useApiResource(load);
  if (error) return <ErrorState title="Quote not available" description={error.message} onRetry={retry}/>;
  if (!quote) return <LoadingState label="Loading quote"/>;
  return <><a className="account-back" href="/account/quotes">← Back to quotes</a><div className="detail-hero"><div><Badge variant={quoteVariant(quote.status)}>{quote.status.replaceAll("_", " ")}</Badge><h1>Additional work request</h1><p>Quote {quote.id}</p></div><div className="detail-hero__amount"><small>Total</small><Price amount={quote.total_minor / 100} currency={quote.currency}/></div></div><div className="account-grid"><div className="account-col-8"><Card className="detail-section"><h2>Proposed work</h2><p>{quote.description}</p><table className="quote-lines"><thead><tr><th>Description</th><th>Qty</th><th>Amount</th></tr></thead><tbody>{quote.line_items.map((line, index) => <tr key={`${line.description}-${index}`}><td>{line.description}</td><td>{line.quantity}</td><td>{new Intl.NumberFormat("en-GB", { style: "currency", currency: quote.currency }).format(line.quantity * line.unit_price_minor / 100)}</td></tr>)}</tbody></table><div className="quote-totals"><div><span>Subtotal</span><span>{new Intl.NumberFormat("en-GB", { style: "currency", currency: quote.currency }).format(quote.subtotal_minor / 100)}</span></div><div><span>Tax</span><span>{new Intl.NumberFormat("en-GB", { style: "currency", currency: quote.currency }).format(quote.tax_minor / 100)}</span></div><div><span>Total</span><strong>{new Intl.NumberFormat("en-GB", { style: "currency", currency: quote.currency }).format(quote.total_minor / 100)}</strong></div></div></Card></div><Card className="account-col-4 approval-panel">{quote.status === "PENDING_CUSTOMER" ? <QuoteApproval quoteId={quote.id} amountMinor={quote.total_minor} currency={quote.currency}/> : <div className="approval-success"><Badge variant={quoteVariant(quote.status)}>{quote.status.replaceAll("_", " ")}</Badge><h2>No action needed</h2><p>This quote has already been decided.</p></div>}</Card></div></>;
}

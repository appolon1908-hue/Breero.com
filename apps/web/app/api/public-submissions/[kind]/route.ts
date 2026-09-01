import { NextRequest, NextResponse } from "next/server";
import { forwardedHeaders, proxyApiRequest } from "@/lib/server-api";

const endpoints = {
  "service-requests": "/service-requests",
  contact: "/contact",
  "provider-interest": "/provider-interest",
} as const;

export async function POST(request: NextRequest, context: { params: Promise<{ kind: string }> }) {
  const { kind } = await context.params;
  const endpoint = endpoints[kind as keyof typeof endpoints];
  if (!endpoint) return NextResponse.json({ detail: "Unknown submission type." }, { status: 404 });
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ detail: "A valid JSON request is required." }, { status: 400 });
  }
  return proxyApiRequest(request, endpoint, {
    method: "POST",
    headers: forwardedHeaders(request, {
      "Idempotency-Key": request.headers.get("idempotency-key") ?? crypto.randomUUID(),
    }),
    body: JSON.stringify(body),
  });
}

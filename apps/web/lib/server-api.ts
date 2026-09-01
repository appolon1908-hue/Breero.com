import "server-only";
import { NextRequest, NextResponse } from "next/server";

const DEFAULT_API = "https://api.breero.com/api/v1";

export function serverApiBase(): string {
  return (
    process.env.BREERO_API_INTERNAL_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    DEFAULT_API
  ).replace(/\/$/, "");
}

export async function proxyApiRequest(
  request: NextRequest,
  path: string,
  init: RequestInit = {},
): Promise<NextResponse> {
  try {
    const response = await fetch(`${serverApiBase()}${path}`, {
      ...init,
      cache: "no-store",
      signal: AbortSignal.timeout(12_000),
    });
    const contentType = response.headers.get("content-type") ?? "";
    const body =
      response.status === 204
        ? null
        : contentType.includes("application/json")
          ? await response.json()
          : { detail: await response.text() };
    return body === null
      ? new NextResponse(null, { status: response.status })
      : NextResponse.json(body, { status: response.status });
  } catch {
    return NextResponse.json(
      { detail: "The BREERO service is temporarily unavailable. Please try again." },
      { status: 503 },
    );
  }
}

export function forwardedHeaders(request: NextRequest, extra: HeadersInit = {}): Headers {
  const headers = new Headers(extra);
  headers.set("content-type", "application/json");
  const userAgent = request.headers.get("user-agent");
  if (userAgent) headers.set("user-agent", userAgent);
  const forwardedFor = request.headers.get("x-forwarded-for");
  if (forwardedFor) headers.set("x-forwarded-for", forwardedFor);
  return headers;
}

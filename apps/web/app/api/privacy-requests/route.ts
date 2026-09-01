import { NextRequest } from "next/server";
import { forwardedHeaders, proxyApiRequest } from "@/lib/server-api";
export async function POST(request: NextRequest) {
  const form = await request.formData();
  return proxyApiRequest(request, "/privacy-requests", {
    method: "POST",
    headers: forwardedHeaders(request),
    body: JSON.stringify({
      requestType: form.get("requestType"),
      email: form.get("email"),
      gpc: request.headers.get("sec-gpc") === "1",
    }),
  });
}

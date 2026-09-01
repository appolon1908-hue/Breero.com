import { NextRequest } from "next/server";
import { forwardedHeaders, proxyApiRequest } from "@/lib/server-api";
export async function POST(request: NextRequest) {
  const form = await request.formData();
  const checked = (name: string) => form.get(name) === "on";
  return proxyApiRequest(request, "/communications/preferences", {
    method: "POST",
    headers: forwardedHeaders(request),
    body: JSON.stringify({
      destination: form.get("destination"),
      transactionalEmail: checked("transactionalEmail"),
      transactionalSms: checked("transactionalSms"),
      marketingEmail: checked("marketingEmail"),
      marketingSms: checked("marketingSms"),
      source_url: new URL("/communications-preferences", request.url).toString(),
      disclosure_text:
        "I choose the separately listed BREERO communication purposes. Marketing is not required for service and is currently disabled.",
      policy_versions: { communications: "2026.08.13", privacy: "2026.08.13", sms: "2026.08.13" },
    }),
  });
}

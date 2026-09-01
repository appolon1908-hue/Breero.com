"use client";

import { FormEvent, useEffect, useState } from "react";
import type { PublicCapabilities } from "@breero/types";

type FormKind = "service" | "contact" | "provider";
type Service = { id: string; slug: string; name: string; is_active?: boolean };
type AddressValidation = { serviceable: boolean; formatted_address: string };

function value(data: FormData, key: string) {
  return String(data.get(key) ?? "").trim();
}

export function PublicIntakeForm({ kind }: { kind: FormKind }) {
  const [services, setServices] = useState<Service[]>([]);
  const [catalogError, setCatalogError] = useState(false);
  const [capabilities, setCapabilities] = useState<PublicCapabilities | null>(null);
  const [state, setState] = useState<"idle" | "sending" | "accepted" | "unserviceable" | "error">(
    "idle",
  );

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/capabilities", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("capabilities unavailable");
        return response.json() as Promise<PublicCapabilities>;
      })
      .then(setCapabilities)
      .catch((error: unknown) => {
        if ((error as { name?: string }).name !== "AbortError") setCatalogError(true);
      });
    if (kind !== "service") return () => controller.abort();
    fetch("/api/services", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("catalog unavailable");
        return response.json() as Promise<Service[]>;
      })
      .then((items) => setServices(items.filter((item) => item.is_active !== false)))
      .catch((error: unknown) => {
        if ((error as { name?: string }).name !== "AbortError") setCatalogError(true);
      });
    return () => controller.abort();
  }, [kind]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (kind === "service" && !capabilities?.request_intake) {
      setState("error");
      return;
    }
    const form = event.currentTarget;
    setState("sending");
    const data = new FormData(form);
    const source = new URL(window.location.href);
    const shared = {
      source_url: window.location.href,
      company: value(data, "company"),
      utm_source: source.searchParams.get("utm_source") ?? undefined,
      utm_medium: source.searchParams.get("utm_medium") ?? undefined,
      utm_campaign: source.searchParams.get("utm_campaign") ?? undefined,
      utm_content: source.searchParams.get("utm_content") ?? undefined,
      utm_term: source.searchParams.get("utm_term") ?? undefined,
      customer_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      transactional_contact_allowed: data.get("transactional_contact_allowed") === "on",
      transactional_email_consent: data.get("transactional_email_consent") === "on",
      transactional_sms_consent: data.get("transactional_sms_consent") === "on",
      marketing_email_consent: data.get("marketing_email_consent") === "on",
      marketing_sms_consent: data.get("marketing_sms_consent") === "on",
      consent_disclosures: {
        transactional_sms:
          "I agree to receive recurring automated appointment and service-status text messages from BREERO at the number provided. Message frequency varies. Message and data rates may apply. Reply STOP to opt out or HELP for help. Consent is not a condition of purchase.",
        marketing_sms:
          "I agree to receive recurring automated promotional and marketing text messages from BREERO at the number provided. Message frequency varies. Message and data rates may apply. Reply STOP to opt out or HELP for help. Consent is not a condition of purchase. Marketing SMS is currently disabled.",
      },
      marketing_consent: false,
      sms_consent: false,
      email_consent: false,
      consent_timestamp: new Date().toISOString(),
      consent_source: "breero_public_intake",
      policy_version: "2026-08-13-request-only",
    };
    const payload =
      kind === "service"
        ? {
            ...shared,
            name: value(data, "name"),
            email: value(data, "email"),
            phone: value(data, "phone"),
            service_slug: value(data, "service_slug"),
            service_description: value(data, "message"),
            address_line1: value(data, "address_line1"),
            city: value(data, "city"),
            state: value(data, "state"),
            postal_code: value(data, "postal_code"),
            requested_date: value(data, "requested_date") || undefined,
            requested_timing: value(data, "requested_time") || undefined,
            contact_preference: value(data, "contact_preference"),
          }
        : kind === "contact"
          ? {
              ...shared,
              name: value(data, "name"),
              email: value(data, "email"),
              phone: value(data, "phone") || undefined,
              category: value(data, "category"),
              subject: value(data, "subject"),
              message: value(data, "message"),
            }
          : {
              ...shared,
              business_name: value(data, "business_name"),
              contact_name: value(data, "contact_name"),
              email: value(data, "email"),
              phone: value(data, "phone"),
              business_website: value(data, "business_website") || undefined,
              service_categories: [value(data, "service_category")],
              city: value(data, "city"),
              state: value(data, "state"),
              postal_code: value(data, "postal_code"),
              license_details: value(data, "license_details") || undefined,
              notes: value(data, "message") || undefined,
            };
    const endpoint =
      kind === "service"
        ? "service-requests"
        : kind === "contact"
          ? "contact"
          : "provider-interest";
    try {
      if (kind === "service") {
        const address = [
          value(data, "address_line1"),
          value(data, "city"),
          value(data, "state"),
          value(data, "postal_code"),
          "US",
        ].join(", ");
        const validation = await fetch("/api/addresses/validate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ address }),
        }).catch(() => null);
        // Geocoding may be disabled or temporarily unavailable during the request-only release.
        // In that case the operator performs the authoritative address review after intake.
        if (validation?.ok) {
          const result = (await validation.json()) as AddressValidation;
          if (!result.serviceable) {
            setState("unserviceable");
            return;
          }
        }
      }
      const response = await fetch(`/api/public-submissions/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() },
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error("submission failed");
      setState("accepted");
      form.reset();
    } catch {
      setState("error");
    }
  }

  return (
    <form className="mk-intake" onSubmit={submit} aria-busy={state === "sending"}>
      <div className="mk-intake__honeypot" aria-hidden="true">
        <label>
          Company website
          <input name="company" tabIndex={-1} autoComplete="off" />
        </label>
      </div>
      {kind === "provider" ? (
        <>
          <label>
            Business name
            <input name="business_name" required minLength={2} />
          </label>
          <label>
            Contact name
            <input name="contact_name" required minLength={2} autoComplete="name" />
          </label>
        </>
      ) : (
        <label>
          Name
          <input name="name" required minLength={2} autoComplete="name" />
        </label>
      )}
      <label>
        Email
        <input name="email" type="email" required autoComplete="email" />
      </label>
      <label>
        Phone
        <input name="phone" type="tel" required={kind !== "contact"} autoComplete="tel" />
      </label>
      {kind === "service" && (
        <>
          <label>
            Service
            <select name="service_slug" required disabled={!services.length}>
              {services.length ? (
                services.map((service) => (
                  <option key={service.id} value={service.slug}>
                    {service.name}
                  </option>
                ))
              ) : (
                <option>Loading live services…</option>
              )}
            </select>
          </label>
          {catalogError && (
            <p role="alert">Live services are unavailable right now. Please try again shortly.</p>
          )}
          <label>
            Street address
            <input name="address_line1" required autoComplete="street-address" />
          </label>
          <label>
            City
            <input name="city" required autoComplete="address-level2" />
          </label>
          <label>
            State or district
            <select name="state" required autoComplete="address-level1">
              <option value="">Select state</option>
              {[
                "AL",
                "AK",
                "AZ",
                "AR",
                "CA",
                "CO",
                "CT",
                "DE",
                "DC",
                "FL",
                "GA",
                "HI",
                "ID",
                "IL",
                "IN",
                "IA",
                "KS",
                "KY",
                "LA",
                "ME",
                "MD",
                "MA",
                "MI",
                "MN",
                "MS",
                "MO",
                "MT",
                "NE",
                "NV",
                "NH",
                "NJ",
                "NM",
                "NY",
                "NC",
                "ND",
                "OH",
                "OK",
                "OR",
                "PA",
                "RI",
                "SC",
                "SD",
                "TN",
                "TX",
                "UT",
                "VT",
                "VA",
                "WA",
                "WV",
                "WI",
                "WY",
              ].map((code) => (
                <option key={code} value={code}>
                  {code}
                </option>
              ))}
            </select>
          </label>
          <label>
            ZIP code
            <input
              name="postal_code"
              required
              pattern="[0-9]{5}(-[0-9]{4})?"
              autoComplete="postal-code"
            />
          </label>
          <label>
            Preferred date (request only)
            <input name="requested_date" type="date" required />
          </label>
          <label>
            Preferred local time (request only)
            <input name="requested_time" type="time" min="07:00" max="19:00" required />
          </label>
          <label>
            Contact preference
            <select name="contact_preference">
              <option value="email">Email</option>
              <option value="phone">Phone</option>
              <option value="text">Text</option>
            </select>
          </label>
        </>
      )}
      {kind === "contact" && (
        <>
          <label>
            Category
            <select name="category">
              <option value="booking_help">Booking help</option>
              <option value="service_issue">Service issue</option>
              <option value="billing">Billing</option>
              <option value="general">General</option>
              <option value="business">Business</option>
            </select>
          </label>
          <label>
            Subject
            <input name="subject" required minLength={3} />
          </label>
          <label>
            Message
            <textarea name="message" required minLength={5} maxLength={4000} />
          </label>
        </>
      )}
      {kind === "provider" && (
        <>
          <label>
            Website <span>(optional)</span>
            <input name="business_website" type="url" />
          </label>
          <label>
            Primary service
            <select name="service_category">
              {[
                "plumbing",
                "electrical",
                "handyman",
                "heating",
                "cooling",
                "appliance-repair",
                "cleaning",
                "locksmith",
                "painting",
                "carpentry",
                "moving-help",
                "home-maintenance",
              ].map((slug) => (
                <option key={slug} value={slug}>
                  {slug.replaceAll("-", " ")}
                </option>
              ))}
            </select>
          </label>
          <label>
            City
            <input name="city" required autoComplete="address-level2" />
          </label>
          <label>
            State or district
            <select name="state" required autoComplete="address-level1">
              <option value="">Select state</option>
              {[
                "AL",
                "AK",
                "AZ",
                "AR",
                "CA",
                "CO",
                "CT",
                "DE",
                "DC",
                "FL",
                "GA",
                "HI",
                "ID",
                "IL",
                "IN",
                "IA",
                "KS",
                "KY",
                "LA",
                "ME",
                "MD",
                "MA",
                "MI",
                "MN",
                "MS",
                "MO",
                "MT",
                "NE",
                "NV",
                "NH",
                "NJ",
                "NM",
                "NY",
                "NC",
                "ND",
                "OH",
                "OK",
                "OR",
                "PA",
                "RI",
                "SC",
                "SD",
                "TN",
                "TX",
                "UT",
                "VT",
                "VA",
                "WA",
                "WV",
                "WI",
                "WY",
              ].map((code) => (
                <option key={code} value={code}>
                  {code}
                </option>
              ))}
            </select>
          </label>
          <label>
            ZIP code
            <input
              name="postal_code"
              required
              pattern="[0-9]{5}(-[0-9]{4})?"
              autoComplete="postal-code"
            />
          </label>
          <label>
            License information <span>(when applicable)</span>
            <input name="license_details" maxLength={1000} />
          </label>
        </>
      )}
      {(kind === "service" || kind === "provider") && (
        <label>
          {kind === "service" ? "What do you need help with?" : "Anything else we should know?"}
          <textarea
            name="message"
            required={kind === "service"}
            minLength={kind === "service" ? 5 : undefined}
            maxLength={4000}
          />
        </label>
      )}
      <label>
        <input name="transactional_contact_allowed" type="checkbox" required /> I agree that BREERO
        may contact me about this request. I understand this is not a confirmed appointment.
      </label>
      <fieldset>
        <legend>Optional communications</legend>
        <label>
          <input name="transactional_email_consent" type="checkbox" /> I agree to receive
          appointment and service-status email from BREERO.
        </label>
        <label>
          <input name="transactional_sms_consent" type="checkbox" /> I agree to receive recurring
          automated appointment and service-status text messages from BREERO at the number provided.
          Message frequency varies. Message and data rates may apply. Reply STOP to opt out or HELP
          for help. Consent is not a condition of purchase. See <a href="/sms-terms">SMS Terms</a>{" "}
          and <a href="/privacy">Privacy Policy</a>.
        </label>
        <label>
          <input name="marketing_email_consent" type="checkbox" /> I separately agree to marketing
          email. Marketing email is currently disabled.
        </label>
        <label>
          <input name="marketing_sms_consent" type="checkbox" /> I agree to receive recurring
          automated promotional and marketing text messages from BREERO at the number provided.
          Message frequency varies. Message and data rates may apply. Reply STOP to opt out or HELP
          for help. Consent is not a condition of purchase. Marketing SMS is currently disabled. See{" "}
          <a href="/sms-terms">SMS Terms</a> and <a href="/privacy">Privacy Policy</a>.
        </label>
      </fieldset>
      <p className="mk-intake__disclosure">
        BREERO coordinates requests with independent service providers. Providers remain responsible
        for final estimates, scope, pricing, licensing, permits, insurance, workmanship and service
        performance.
      </p>
      <button
        className="mk-button mk-button--primary"
        type="submit"
        disabled={
          state === "sending" ||
          (kind === "service" &&
            (!capabilities || !services.length || !capabilities.request_intake))
        }
      >
        {state === "sending"
          ? "Sending…"
          : kind === "provider"
            ? "Submit interest"
            : "Send request"}
      </button>
      <div aria-live="polite">
        {state === "accepted" && (
          <p className="mk-intake__success">
            Your request was accepted. This does not yet confirm availability or provider
            assignment.
          </p>
        )}
        {state === "unserviceable" && (
          <p role="alert">
            We could not confirm service coverage for that address. Check the address and ZIP code,
            or contact support@breero.com.
          </p>
        )}
        {state === "error" && (
          <p role="alert">
            We could not accept the request. Please retry or email support@breero.com.
          </p>
        )}
      </div>
    </form>
  );
}

import { LegalPage } from "@/components/marketing/LegalPage";
export default function Page() {
  return (
    <LegalPage title="Service Fulfillment and Appointment Policy" updated="13 August 2026">
      <p>
        BREERO, operated by Codestra LLC, is a service-coordination and lead-generation platform
        connecting customers with independent providers. BREERO does not perform underlying
        contractor or trade work unless a specific offering expressly says otherwise.
      </p>
      <h2>Requests and confirmation</h2>
      <p>
        A preferred date and time is a request, not a confirmed appointment. Availability is not
        guaranteed. Confirmation requires a validated address and time zone, exact ZIP and service
        coverage, current licensing and insurance, working hours and capacity, an atomic slot hold,
        and approval by an authorized operator. Automatic assignment and confirmation are disabled.
      </p>
      <h2>No-capacity fallback</h2>
      <p>
        If no qualified provider or capacity exists, the request remains requested or pending manual
        dispatch. BREERO will not label unsupported work confirmed, assigned, scheduled, or
        completed.
      </p>
      <h2>Hours and emergencies</h2>
      <p>
        Regular request availability is Monday–Saturday, 7:00 a.m.–7:00 p.m. local time. Sunday 7:00
        a.m.–7:00 p.m. is limited to urgent home-service requests. BREERO is not a medical or
        life-safety service; call 911 for life-safety emergencies.
      </p>
      <h2>Provider responsibility</h2>
      <p>
        Independent providers are responsible for workmanship, licensing, permits, insurance,
        estimates, price, scope, safety, and legal compliance. Recommendations are not endorsements
        or guarantees. Final scope, price, and performance are agreed with the provider. All work is
        quote-required; no online payment is required or collected.
      </p>
    </LegalPage>
  );
}

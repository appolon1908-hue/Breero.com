import { LegalPage } from "@/components/marketing/LegalPage";
export default function Page() {
  return (
    <LegalPage title="Independent Provider Terms" updated="13 August 2026">
      <p>
        Providers participate as independent contractors, not employees or agents of BREERO or
        Codestra LLC. They remain responsible for workmanship, estimates, pricing, scope, permits,
        safety, taxes, and legal compliance.
      </p>
      <h2>Eligibility</h2>
      <p>
        Providers must maintain all licensing and insurance required for each service and
        jurisdiction, keep exact ZIP coverage and capacity accurate, and accept work only within
        authorization.
      </p>
      <h2>Customer information</h2>
      <p>
        Customer information may be used only for the requested service and permitted follow-up. It
        may not be resold, scraped, or used for unrelated marketing. Providers must honor
        communication opt-outs and privacy restrictions.
      </p>
      <h2>Scheduling</h2>
      <p>
        A recommendation does not assign a provider. Only an authorized operator may approve final
        assignment and confirmation. Providers must report conflicts, changes, cancellations, and
        completion truthfully.
      </p>
    </LegalPage>
  );
}

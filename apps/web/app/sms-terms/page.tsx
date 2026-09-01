import { LegalPage } from "@/components/marketing/LegalPage";
export default function Page() {
  return (
    <LegalPage title="SMS Terms and Conditions" updated="13 August 2026">
      <p>
        Transactional appointment texts and marketing texts require separate consent. Neither is a
        condition of purchase, and marketing SMS is currently disabled.
      </p>
      <h2>Transactional messages</h2>
      <p>
        If separately authorized, messages may concern a requested appointment, manual dispatch,
        confirmation, rescheduling, cancellation, or service status. Frequency varies; message and
        data rates may apply.
      </p>
      <h2>Opt out and help</h2>
      <p>
        Reply STOP, QUIT, END, REVOKE, OPT OUT, CANCEL, or UNSUBSCRIBE to revoke. Reply HELP for
        support. Reasonable plain-language revocations are also honored. A permitted non-promotional
        confirmation may follow an opt-out.
      </p>
      <h2>Emergencies</h2>
      <p>
        BREERO does not provide medical, emergency, or life-safety services. Call 911 or the
        appropriate emergency authority for a life-safety emergency.
      </p>
    </LegalPage>
  );
}

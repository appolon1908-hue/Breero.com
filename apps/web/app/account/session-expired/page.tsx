import { Card, ClockIcon } from "@breero/ui";
export const metadata = { title: "Session expired" };
export default function SessionExpired() {
  return (
    <div className="center-state">
      <Card className="session-card">
        <span>
          <ClockIcon size={28} />
        </span>
        <h1>Your session has expired</h1>
        <p>
          For your security, we signed you out after a period of inactivity. Your bookings and
          changes are safe.
        </p>
        <a className="br-button br-button--primary br-button--md" href="/account/login">
          Sign in again
        </a>
      </Card>
    </div>
  );
}

import { Card, ShieldIcon } from "@breero/ui";
export const metadata = { title: "Access unavailable" };
export default function Forbidden() {
  return (
    <div className="center-state">
      <Card className="session-card">
        <span>
          <ShieldIcon size={28} />
        </span>
        <h1>This area isn’t available</h1>
        <p>
          Your account doesn’t have access to this page. If this seems wrong, our support team can
          help.
        </p>
        <a className="br-button br-button--outline br-button--md" href="/help">
          Contact support
        </a>
      </Card>
    </div>
  );
}

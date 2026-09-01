import { Card, ShieldIcon } from "@breero/ui";
export const metadata = { title: "Sign in required" };
export default function Unauthorized() {
  return (
    <div className="center-state">
      <Card className="session-card">
        <span>
          <ShieldIcon size={28} />
        </span>
        <h1>Sign in to continue</h1>
        <p>This page contains your personal booking information. Please sign in to view it.</p>
        <a className="br-button br-button--primary br-button--md" href="/account/login">
          Go to sign in
        </a>
      </Card>
    </div>
  );
}

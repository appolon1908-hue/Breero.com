import { Card } from "@breero/ui";
import { AccountPageHeader } from "@/components/account/page-header";
import { ProfileForm } from "@/components/account/profile-form";
export const metadata = { title: "Profile & settings" };
export default function ProfilePage() {
  return (
    <>
      <AccountPageHeader
        eyebrow="Your details"
        title="Profile & settings"
        description="Keep your contact details and communication preferences up to date."
      />
      <div className="account-grid">
        <Card className="account-col-7 detail-section">
          <h2>Personal information</h2>
          <ProfileForm />
        </Card>
        <Card className="account-col-5 detail-section">
          <h2>Account security</h2>
          <p>Your account email is verified.</p>
          <div className="detail-actions">
            <a
              className="br-button br-button--outline br-button--md"
              href="/account/reset-password"
            >
              Change password
            </a>
            <a href="/account/addresses">Manage saved addresses →</a>
          </div>
          <div className="support-path">
            <strong>Privacy controls</strong>
            <span>Contact support to request an export or deletion of your account.</span>
            <a href="/privacy">Read our privacy policy →</a>
          </div>
        </Card>
      </div>
    </>
  );
}

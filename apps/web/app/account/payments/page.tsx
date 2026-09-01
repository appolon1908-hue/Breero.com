import { Card } from "@breero/ui";
import { AccountPageHeader } from "@/components/account/page-header";
export default function PaymentsPage() {
  return (
    <>
      <AccountPageHeader
        eyebrow="Payments disabled"
        title="No online payments"
        description="BREERO does not currently require or collect online payment."
      />
      <Card>
        <h2>All work is quote-required</h2>
        <p>
          Checkout, charges, refunds, subscriptions, payouts, and paid-lead processing are disabled.
          Any price and payment terms for underlying work are agreed directly with the independent
          provider unless BREERO expressly states otherwise in a future, separately authorized
          offering.
        </p>
      </Card>
    </>
  );
}

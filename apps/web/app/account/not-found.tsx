import Link from "next/link";
import { EmptyState } from "@breero/ui";
export default function AccountNotFound() {
  return (
    <EmptyState
      title="We couldn’t find that"
      description="It may have been removed, or it may belong to a different account."
      action={
        <Link className="br-button br-button--outline br-button--md" href="/account">
          Back to my account
        </Link>
      }
    />
  );
}

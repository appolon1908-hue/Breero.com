import { AuthCard } from "@/components/account/auth-card";
import { AuthForm } from "@/components/account/auth-form";
export const metadata = { title: "Choose a new password" };
export default function Reset() {
  return (
    <AuthCard
      title="Choose a new password"
      description="Make it memorable, unique and at least eight characters long."
    >
      <AuthForm mode="reset" />
    </AuthCard>
  );
}

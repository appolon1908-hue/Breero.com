import { AuthCard } from "@/components/account/auth-card";
import { AuthForm } from "@/components/account/auth-form";
export const metadata = { title: "Forgot password" };
export default function Forgot() {
  return (
    <AuthCard
      title="Reset your password"
      description="Enter your email and we’ll send instructions if it matches a BREERO account."
      footer={<a href="/account/login">← Back to sign in</a>}
    >
      <AuthForm mode="forgot" />
    </AuthCard>
  );
}

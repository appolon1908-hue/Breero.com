import { AuthCard } from "@/components/account/auth-card";
import { AuthForm } from "@/components/account/auth-form";
export const metadata = { title: "Sign in" };
export default function Login() {
  return (
    <AuthCard
      eyebrow="Welcome back"
      title="Sign in to BREERO"
      description="Access your protected request history and profile."
      footer={<>Account creation is controlled during this release.</>}
    >
      <AuthForm mode="login" />
    </AuthCard>
  );
}

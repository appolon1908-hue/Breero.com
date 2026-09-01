import { AuthCard } from "@/components/account/auth-card";
import { AuthForm } from "@/components/account/auth-form";
export const metadata = { title: "Create an account" };
export default function Register() {
  return (
    <AuthCard
      eyebrow="Join BREERO"
      title="A simpler way to care for home"
      description="Create your account to manage every service from request to receipt."
      footer={
        <>
          Already have an account? <a href="/account/login">Sign in</a>
        </>
      }
    >
      <AuthForm mode="register" />
    </AuthCard>
  );
}

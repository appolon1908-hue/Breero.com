import { AuthCard } from "@/components/account/auth-card";
import { AuthForm } from "@/components/account/auth-form";
export const metadata = { title: "Verify email" };
export default function Verify() {
  return (
    <AuthCard
      eyebrow="Almost there"
      title="Verify your email"
      description="Confirm your address to protect your bookings and receive important service updates."
    >
      <AuthForm mode="verify" />
    </AuthCard>
  );
}

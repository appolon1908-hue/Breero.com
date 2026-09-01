import type { Metadata } from "next";
import { PublicIntakeForm } from "@/components/marketing/PublicIntakeForm";

export const metadata: Metadata = {
  title: "Request a home service",
  description: "Tell BREERO what your home needs and submit a service coordination request.",
  alternates: { canonical: "/request-service" },
};

export default function Page() {
  return (
    <section className="mk-section mk-section--sky">
      <div className="mk-container mk-narrow">
        <header className="mk-heading">
          <p className="mk-eyebrow">Request service</p>
          <h1>Tell us what your home needs.</h1>
          <p>
            This request starts coordination. It is not a confirmed booking, provider assignment,
            price or appointment.
          </p>
        </header>
        <PublicIntakeForm kind="service" />
      </div>
    </section>
  );
}

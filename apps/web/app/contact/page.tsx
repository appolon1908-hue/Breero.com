import type { Metadata } from "next";
import { StandardPage } from "@/components/marketing/StandardPage";
import { PublicIntakeForm } from "@/components/marketing/PublicIntakeForm";
import { corePages } from "@/content/pages/core";
export const metadata: Metadata = {
  title: "Contact BREERO",
  description: corePages.contact.description,
  alternates: { canonical: "/contact" },
};
export default function Page() {
  return (
    <StandardPage content={corePages.contact}>
      <section className="mk-section mk-section--cream">
        <div className="mk-container mk-narrow">
          <header className="mk-heading">
            <p className="mk-eyebrow">Customer and business support</p>
            <h2>Send us the details.</h2>
            <p>
              Include your booking, request, or lead reference when available. Never send passwords
              or payment credentials.
            </p>
          </header>
          <PublicIntakeForm kind="contact" />
        </div>
      </section>
    </StandardPage>
  );
}

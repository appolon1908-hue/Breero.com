import type { Metadata } from "next";
import { StandardPage } from "@/components/marketing/StandardPage";
import { PublicIntakeForm } from "@/components/marketing/PublicIntakeForm";
import { corePages } from "@/content/pages/core";
export const metadata: Metadata = {
  title: "Partner with BREERO",
  description: corePages.partners.description,
  alternates: { canonical: "/partners" },
};
export default function Page() {
  return (
    <StandardPage content={corePages.partners}>
      <section id="interest" className="mk-section mk-section--cream">
        <div className="mk-container mk-narrow">
          <header className="mk-heading">
            <p className="mk-eyebrow">Provider interest</p>
            <h2>Tell us about your service business.</h2>
            <p>
              Submitting interest does not promise approval, leads, jobs or earnings. No provider
              portal exists yet.
            </p>
          </header>
          <PublicIntakeForm kind="provider" />
        </div>
      </section>
    </StandardPage>
  );
}

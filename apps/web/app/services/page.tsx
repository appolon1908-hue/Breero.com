import type { Metadata } from "next";
import { Hero } from "@/components/marketing/Hero";
import { ServiceGrid } from "@/components/marketing/ServiceGrid";
import { TrustBar } from "@/components/marketing/TrustBar";
import { CTASection } from "@/components/marketing/CTASection";
import { images } from "@/content/images";
export const metadata: Metadata = {
  title: "Home services",
  description: "Explore trusted help for repairs, maintenance and everyday home services.",
  alternates: { canonical: "/services" },
};
export default function Services() {
  return (
    <>
      <Hero
        compact
        eyebrow="Services for your home"
        title="The right help starts here."
        description="Explore home services, understand what to expect and enter one clear booking flow."
        image={images.servicesHero}
      />
      <TrustBar />
      <section className="mk-section">
        <div className="mk-container">
          <header className="mk-heading">
            <p className="mk-eyebrow">Service directory</p>
            <h2>What does your home need?</h2>
            <p>
              Bookable services are connected to the current catalog. Other pages explain planned
              categories without claiming live availability.
            </p>
          </header>
          <ServiceGrid />
        </div>
      </section>
      <CTASection />
    </>
  );
}

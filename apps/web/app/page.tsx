import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { brand } from "@/content/brand";
import { images } from "@/content/images";
import { Hero } from "@/components/marketing/Hero";
import { ServiceDiscovery } from "@/components/marketing/ServiceDiscovery";
import { TrustBar } from "@/components/marketing/TrustBar";
import { ServiceGrid } from "@/components/marketing/ServiceGrid";
import { HowItWorks } from "@/components/marketing/HowItWorks";
import { WhyBreero } from "@/components/marketing/WhyBreero";
import { TestimonialGrid } from "@/components/marketing/TestimonialGrid";
import { Guarantee } from "@/components/marketing/Guarantee";
import { FAQ } from "@/components/marketing/FAQ";
import { CTASection } from "@/components/marketing/CTASection";
import { JsonLd } from "@/components/seo/JsonLd";

export const metadata: Metadata = {
  title: "Home services, without the hassle",
  description: brand.description,
  alternates: { canonical: "/" },
};
export default function HomePage() {
  return (
    <>
      <JsonLd
        data={[
          {
            "@context": "https://schema.org",
            "@type": "Organization",
            name: "BREERO",
            url: "https://breero.com",
            logo: "https://breero.com/brand/breero-logo-primary.svg",
          },
          {
            "@context": "https://schema.org",
            "@type": "WebSite",
            name: "BREERO",
            url: "https://breero.com",
          },
        ]}
      />
      <Hero title={brand.headline} description={brand.description} image={images.homeHero} />
      <ServiceDiscovery />
      <TrustBar />
      <section className="mk-section">
        <div className="mk-container">
          <header className="mk-heading">
            <p className="mk-eyebrow">Popular services</p>
            <h2>Good help, without the hunt.</h2>
            <p>Choose the work you need, then follow one clear booking journey.</p>
          </header>
          <ServiceGrid limit={6} />
          <div className="mk-actions">
            <Link
              className="mk-button mk-button--secondary"
              href="/services"
              data-cta="home-all-services"
            >
              View all services
            </Link>
          </div>
        </div>
      </section>
      <HowItWorks />
      <section className="mk-section mk-section--cream">
        <div className="mk-container mk-split">
          <div>
            <p className="mk-eyebrow">Designed for real life</p>
            <h2>Know what happens next.</h2>
            <p className="mk-lead">
              Clear steps, an agreed arrival window and booking status that comes from the
              platform—not guesswork.
            </p>
            <Link className="mk-button mk-button--primary" href="/how-it-works">
              See how it works
            </Link>
          </div>
          <div className="mk-image-panel">
            <Image
              src={images.technicianArrival.src}
              alt={images.technicianArrival.alt}
              fill
              sizes="(max-width: 768px) 100vw, 48vw"
              className="mk-cover"
            />
          </div>
        </div>
      </section>
      <WhyBreero />
      <TestimonialGrid />
      <Guarantee />
      <section className="mk-section">
        <div className="mk-container mk-split">
          <div>
            <p className="mk-eyebrow">Supported locations</p>
            <h2>Coverage is checked, never assumed.</h2>
            <p className="mk-lead">
              Enter your address during booking. BREERO checks exact serviceability and availability
              securely.
            </p>
            <Link className="mk-button mk-button--secondary" href="/locations">
              About service areas
            </Link>
          </div>
          <div className="mk-image-panel mk-image-panel--landscape">
            <Image
              src={images.localCommunity.src}
              alt={images.localCommunity.alt}
              fill
              sizes="(max-width: 768px) 100vw, 46vw"
              className="mk-cover"
            />
          </div>
        </div>
      </section>
      <section className="mk-cta mk-cta--warm">
        <div className="mk-container">
          <div>
            <p className="mk-eyebrow">Your home, handled</p>
            <h2>Ready to get the job moving?</h2>
            <p>
              Choose a service, tell us what is happening and check live availability for your
              address.
            </p>
          </div>
          <Link className="mk-button mk-button--primary" href="/booking" data-cta="homeowner-book">
            Book a service
          </Link>
        </div>
      </section>
      <section className="mk-section mk-section--navy">
        <div className="mk-container mk-split">
          <div>
            <p className="mk-eyebrow">For professionals</p>
            <h2>Do great work. We’ll help with the rest.</h2>
            <p className="mk-lead">
              Learn about the standards and process for service businesses interested in BREERO.
            </p>
            <Link
              className="mk-button mk-button--light"
              href="/partners"
              data-cta="partner-interest"
            >
              Partner information
            </Link>
          </div>
          <div className="mk-image-panel mk-image-panel--landscape">
            <Image
              src={images.partnerProfessional.src}
              alt={images.partnerProfessional.alt}
              fill
              sizes="(max-width: 768px) 100vw, 46vw"
              className="mk-cover"
            />
          </div>
        </div>
      </section>
      <section className="mk-section mk-section--sky">
        <div className="mk-container mk-narrow">
          <header className="mk-heading">
            <p className="mk-eyebrow">Frequently asked</p>
            <h2>Straight answers.</h2>
          </header>
          <FAQ limit={5} />
        </div>
      </section>
      <CTASection />
    </>
  );
}

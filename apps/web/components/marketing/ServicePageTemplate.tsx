import Image from "next/image";
import Link from "next/link";
import type { MarketingService } from "@/content/services";
import { images } from "@/content/images";
import { TrustBar } from "./TrustBar";
import { HowItWorks } from "./HowItWorks";
import { FAQ } from "./FAQ";
import { CTASection } from "./CTASection";
import { JsonLd } from "@/components/seo/JsonLd";
export function ServicePageTemplate({ service }: { service: MarketingService }) {
  const booking = service.bookingServiceId
    ? `/booking?service=${service.bookingServiceId}`
    : "/booking";
  return (
    <>
      <JsonLd
        data={[
          {
            "@context": "https://schema.org",
            "@type": "Service",
            name: service.name,
            description: service.description,
            provider: { "@type": "Organization", name: "BREERO" },
          },
          {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            itemListElement: [
              {
                "@type": "ListItem",
                position: 1,
                name: "Services",
                item: "https://breero.com/services",
              },
              {
                "@type": "ListItem",
                position: 2,
                name: service.name,
                item: `https://breero.com/services/${service.slug}`,
              },
            ],
          },
        ]}
      />
      <nav className="mk-breadcrumb mk-container" aria-label="Breadcrumb">
        <Link href="/services">Services</Link>
        <span aria-hidden="true">/</span>
        <span aria-current="page">{service.name}</span>
      </nav>
      <section className="mk-service-hero">
        <div className="mk-container mk-service-hero__grid">
          <div>
            <p className="mk-eyebrow">BREERO {service.name.toLowerCase()}</p>
            <h1>{service.name}, without the runaround.</h1>
            <p className="mk-lead">
              {service.promise} {service.description}
            </p>
            <div className="mk-actions">
              <Link
                className="mk-button mk-button--primary"
                href={booking}
                data-cta={`service-book-${service.slug}`}
              >
                {service.bookingServiceId ? "Book now" : "Check availability"}
              </Link>
              <a className="mk-button mk-button--secondary" href="#included">
                What’s included
              </a>
            </div>
            {!service.bookingServiceId && (
              <p className="mk-availability-note">
                This service is informational until live catalog availability is confirmed for your
                address.
              </p>
            )}
          </div>
          <div className="mk-service-hero__image">
            <Image
              src={service.image.src}
              alt={service.image.alt}
              fill
              priority
              sizes="(max-width: 768px) 100vw, 48vw"
              className="mk-cover"
            />
          </div>
        </div>
      </section>
      <TrustBar />
      <section className="mk-section">
        <div className="mk-container mk-three">
          <article>
            <p className="mk-eyebrow">Common problems</p>
            <h2>When to get help</h2>
            <ul>
              {service.problems.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
          <article id="included">
            <p className="mk-eyebrow">What’s included</p>
            <h2>A professional visit</h2>
            <ul>
              {service.included.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
          <article>
            <p className="mk-eyebrow">Before the visit</p>
            <h2>Simple preparation</h2>
            <p>{service.preparation}</p>
          </article>
        </div>
      </section>
      <HowItWorks />
      <section className="mk-section">
        <div className="mk-container mk-split">
          <div className="mk-image-panel">
            <Image
              src={images.technicianWorking.src}
              alt={images.technicianWorking.alt}
              fill
              sizes="(max-width: 768px) 100vw, 46vw"
              className="mk-cover"
            />
          </div>
          <div>
            <p className="mk-eyebrow">Why BREERO</p>
            <h2>A professional process, kept clear.</h2>
            <p className="mk-lead">
              The booking flow records your request, checks your address and shows authoritative
              availability. Professionals receive the details needed to prepare for the visit.
            </p>
            <div className="mk-feature-list">
              <article>
                <span>1</span>
                <div>
                  <h3>Relevant details</h3>
                  <p>Questions are shaped around the selected service.</p>
                </div>
              </article>
              <article>
                <span>2</span>
                <div>
                  <h3>Professional standards</h3>
                  <p>Clear scope, careful work areas and a tidy handover.</p>
                </div>
              </article>
              <article>
                <span>3</span>
                <div>
                  <h3>Visible next steps</h3>
                  <p>Booking and payment status come from BREERO’s authoritative records.</p>
                </div>
              </article>
            </div>
          </div>
        </div>
      </section>
      <section className="mk-section mk-section--cream">
        <div className="mk-container mk-split">
          <div>
            <p className="mk-eyebrow">Pricing and service area</p>
            <h2>Clear before you commit.</h2>
            <p className="mk-lead">
              Availability, scope and the authoritative amount and currency are shown during
              booking. If extra work is needed later, it requires a separate quote and approval.
            </p>
            <div className="mk-actions">
              <Link className="mk-button mk-button--primary" href={booking}>
                Check your address
              </Link>
              <Link className="mk-button mk-button--secondary" href="/pricing">
                How pricing works
              </Link>
            </div>
          </div>
          <div className="mk-image-panel mk-image-panel--landscape">
            <Image
              src={images.verifiedProfessional.src}
              alt={images.verifiedProfessional.alt}
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
            <p className="mk-eyebrow">Questions about {service.name.toLowerCase()}</p>
            <h2>Straight answers before you book.</h2>
          </header>
          <FAQ limit={5} />
        </div>
      </section>
      <CTASection
        title={`Need ${service.name.toLowerCase()} help?`}
        text="Tell us what is happening and check live coverage for your address."
      />
    </>
  );
}

import Link from "next/link";
import { marketingServices } from "@/content/services";
export function ServiceDiscovery() {
  return (
    <section className="mk-discovery" aria-labelledby="service-discovery-title">
      <div className="mk-container mk-discovery__inner">
        <div>
          <p className="mk-eyebrow">What does your home need?</p>
          <h2 id="service-discovery-title">Start with the job in front of you.</h2>
          <p>
            Choose a category. The booking journey will ask only the details needed to check
            coverage and availability.
          </p>
        </div>
        <nav className="mk-discovery__links" aria-label="Popular service categories">
          {marketingServices.slice(0, 6).map((service) => (
            <Link
              key={service.slug}
              href={`/services/${service.slug}`}
              data-cta={`discovery-${service.slug}`}
            >
              {service.name}
              <span aria-hidden="true">→</span>
            </Link>
          ))}
          <Link className="mk-discovery__all" href="/services">
            Explore all services <span aria-hidden="true">→</span>
          </Link>
        </nav>
      </div>
    </section>
  );
}

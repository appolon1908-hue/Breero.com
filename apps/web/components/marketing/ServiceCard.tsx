import Image from "next/image";
import Link from "next/link";
import type { MarketingService } from "@/content/services";
export function ServiceCard({ service }: { service: MarketingService }) {
  return (
    <Link
      className="mk-service-card"
      href={`/services/${service.slug}`}
      data-cta={`service-card-${service.slug}`}
    >
      <div className="mk-service-card__image">
        <Image
          src={service.image.src}
          alt={service.image.alt}
          fill
          sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
          className="mk-cover"
        />
      </div>
      <div>
        <h3>{service.name}</h3>
        <p>{service.description}</p>
        <span>
          View service <b aria-hidden="true">→</b>
        </span>
      </div>
    </Link>
  );
}

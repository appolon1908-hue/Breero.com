import Image from "next/image";
import Link from "next/link";
import { ctas } from "@/content/cta";

export function Hero({
  eyebrow = "Home care, handled",
  title,
  description,
  image,
  compact = false,
}: {
  eyebrow?: string;
  title: string;
  description: string;
  image: { src: string; alt: string };
  compact?: boolean;
}) {
  return (
    <section className={`mk-hero ${compact ? "mk-hero--compact" : ""}`}>
      <div className="mk-container mk-hero__grid">
        <div className="mk-hero__copy">
          <p className="mk-eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          <p className="mk-lead">{description}</p>
          <div className="mk-actions">
            <Link
              className="mk-button mk-button--primary"
              href={ctas.bookService.href}
              data-cta="hero-book"
            >
              {ctas.bookService.label}
            </Link>
            <Link
              className="mk-button mk-button--secondary"
              href={ctas.exploreServices.href}
              data-cta="hero-services"
            >
              {ctas.exploreServices.label}
            </Link>
          </div>
          <div className="mk-chips" aria-label="BREERO benefits">
            <span>Verified professionals</span>
            <span>Quote required</span>
            <span>No online payment</span>
          </div>
        </div>
        <div className="mk-hero__visual">
          <Image
            src={image.src}
            alt={image.alt}
            fill
            sizes="(max-width: 768px) 100vw, 44vw"
            priority
            className="mk-cover"
          />
          <div className="mk-float mk-float--top">
            <b>Clear from start to finish</b>
            <small>Request before confirmation</small>
          </div>
          <div className="mk-float mk-float--bottom">
            <span aria-hidden="true">●</span>
            <b>Availability verified before confirmation</b>
          </div>
        </div>
      </div>
    </section>
  );
}

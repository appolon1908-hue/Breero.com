import Image from "next/image";
import Link from "next/link";
import { images } from "@/content/images";
export function Guarantee() {
  return (
    <section className="mk-section mk-section--mint">
      <div className="mk-container mk-split">
        <div>
          <p className="mk-eyebrow">Service standards</p>
          <h2>Clear expectations from booking to handover.</h2>
          <p className="mk-lead">
            BREERO keeps the service scope, booking status and support path visible. If something
            needs attention, you know where to go next.
          </p>
          <Link className="mk-button mk-button--secondary" href="/service-guarantee">
            Read our service standards
          </Link>
        </div>
        <div className="mk-image-panel mk-image-panel--landscape">
          <Image
            src={images.serviceGuarantee.src}
            alt={images.serviceGuarantee.alt}
            fill
            sizes="(max-width: 768px) 100vw, 46vw"
            className="mk-cover"
          />
        </div>
      </div>
    </section>
  );
}

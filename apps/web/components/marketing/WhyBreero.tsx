import Image from "next/image";
import { images } from "@/content/images";
const points = [
  {
    title: "Professional standards",
    text: "Service-relevant partner information and qualifications are checked.",
  },
  {
    title: "Authoritative status",
    text: "The platform—not a redirect—confirms payment and booking state.",
  },
  {
    title: "Help when you need it",
    text: "Clear support paths stay available throughout the service.",
  },
];
export function WhyBreero() {
  return (
    <section className="mk-section">
      <div className="mk-container mk-split">
        <div className="mk-image-panel">
          <Image
            src={images.qualityCheck.src}
            alt={images.qualityCheck.alt}
            fill
            sizes="(max-width: 768px) 100vw, 46vw"
            className="mk-cover"
          />
        </div>
        <div>
          <p className="mk-eyebrow">Why BREERO</p>
          <h2>Built around confidence at home.</h2>
          <p className="mk-lead">
            Straightforward booking, trusted professionals and clear next steps—without the
            contractor chase.
          </p>
          <div className="mk-feature-list">
            {points.map((point, i) => (
              <article key={point.title}>
                <span>{i + 1}</span>
                <div>
                  <h3>{point.title}</h3>
                  <p>{point.text}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

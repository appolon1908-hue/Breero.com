import { testimonials } from "@/content/testimonials";
export function TestimonialGrid() {
  const verified = testimonials.filter((item) => item.verified);
  if (!verified.length) return null;
  return (
    <section className="mk-section">
      <div className="mk-container">
        <header className="mk-heading">
          <p className="mk-eyebrow">Customer stories</p>
          <h2>What verified customers say.</h2>
        </header>
        <div className="mk-three">
          {verified.map((item) => (
            <figure key={`${item.name}-${item.quote}`}>
              <blockquote>“{item.quote}”</blockquote>
              <figcaption>
                {item.name} · {item.city} · {item.service}
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}

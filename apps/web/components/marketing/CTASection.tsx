import Link from "next/link";
export function CTASection({
  title = "Your home. Handled.",
  text = "Choose a service and see what is available for your address.",
  secondary = false,
}: {
  title?: string;
  text?: string;
  secondary?: boolean;
}) {
  return (
    <section className={`mk-cta ${secondary ? "mk-cta--warm" : ""}`}>
      <div className="mk-container">
        <div>
          <p className="mk-eyebrow">Ready when you are</p>
          <h2>{title}</h2>
          <p>{text}</p>
        </div>
        <Link className="mk-button mk-button--light" href="/booking" data-cta="section-book">
          Book a service
        </Link>
      </div>
    </section>
  );
}

import type { ReactNode } from "react";
import { Hero } from "./Hero";
import { FAQ } from "./FAQ";
import { CTASection } from "./CTASection";
export type StandardPageContent = {
  eyebrow: string;
  title: string;
  description: string;
  image: { src: string; alt: string };
  sections: Array<{ title: string; text: string }>;
};
export function StandardPage({
  content,
  children,
  faqLimit = 4,
}: {
  content: StandardPageContent;
  children?: ReactNode;
  faqLimit?: number | null;
}) {
  return (
    <>
      <Hero
        compact
        eyebrow={content.eyebrow}
        title={content.title}
        description={content.description}
        image={content.image}
      />
      <section className="mk-section">
        <div className="mk-container mk-copy-grid">
          {content.sections.map((section) => (
            <article key={section.title}>
              <h2>{section.title}</h2>
              <p>{section.text}</p>
            </article>
          ))}
        </div>
      </section>
      {children}
      <section className="mk-section mk-section--cream">
        <div className="mk-container mk-narrow">
          <header className="mk-heading">
            <p className="mk-eyebrow">Helpful answers</p>
            <h2>Good to know.</h2>
          </header>
          <FAQ limit={faqLimit ?? undefined} />
        </div>
      </section>
      <CTASection />
    </>
  );
}

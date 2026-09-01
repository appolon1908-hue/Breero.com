const steps = [
  { n: "01", title: "Choose your service", text: "Find the kind of help your home needs." },
  { n: "02", title: "Tell us what you need", text: "Answer a few relevant questions." },
  { n: "03", title: "Pick a time", text: "Validate your address and see live availability." },
  {
    n: "04",
    title: "We take care of the rest",
    text: "Review, pay securely and follow confirmed status.",
  },
];
export function HowItWorks() {
  return (
    <section className="mk-section mk-section--sky">
      <div className="mk-container">
        <header className="mk-heading">
          <p className="mk-eyebrow">How it works</p>
          <h2>A clear path from “needs doing” to done.</h2>
        </header>
        <div className="mk-steps">
          {steps.map((step) => (
            <article key={step.n}>
              <span>{step.n}</span>
              <h3>{step.title}</h3>
              <p>{step.text}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

const items = [
  "Verified professionals",
  "Quote required",
  "No online payment",
  "Support when you need it",
];
export function TrustBar() {
  return (
    <section className="mk-trustbar" aria-label="Why customers choose BREERO">
      <div className="mk-container">
        {items.map((item) => (
          <div key={item}>
            <span aria-hidden="true">✓</span>
            <strong>{item}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

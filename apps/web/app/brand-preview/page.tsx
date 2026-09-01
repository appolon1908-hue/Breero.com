import { Logo } from "@/components/brand/Logo";
import { BrandMark } from "@/components/brand/BrandMark";
export const metadata = { title: "Brand preview", robots: { index: false, follow: false } };
export default function Page() {
  if (process.env.NODE_ENV === "production")
    return (
      <div className="mk-section">
        <div className="mk-container">
          <h1>Not available</h1>
        </div>
      </div>
    );
  return (
    <div className="mk-section">
      <div className="mk-container">
        <p className="mk-eyebrow">Development only</p>
        <h1>BREERO brand preview</h1>
        <div className="mk-actions">
          <Logo />
          <BrandMark size={64} />
        </div>
        <div className="brand-swatches">
          {[
            "blue",
            "blue-dark",
            "navy",
            "ink",
            "teal",
            "coral",
            "yellow",
            "sky",
            "mint",
            "cream",
            "light",
            "muted",
          ].map((name) => (
            <div key={name} style={{ background: `var(--br-${name})` }}>
              <span>{name}</span>
            </div>
          ))}
        </div>
        <div className="mk-actions">
          <button className="mk-button mk-button--primary" disabled>
            Primary action preview
          </button>
          <button className="mk-button mk-button--secondary" disabled>
            Secondary action preview
          </button>
        </div>
      </div>
    </div>
  );
}

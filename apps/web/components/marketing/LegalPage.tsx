import Link from "next/link";
import { legalBusiness } from "@/content/legal";

export function LegalPage({
  title,
  updated,
  version = "2026.08.13",
  children,
}: {
  title: string;
  updated: string;
  version?: string;
  children: React.ReactNode;
}) {
  return (
    <article className="mk-section">
      <div className="mk-container mk-narrow">
        <p className="mk-eyebrow">BREERO policy</p>
        <h1>{title}</h1>
        <p>
          <strong>Effective:</strong> {updated}
          <br />
          <strong>Last updated:</strong> {updated}
          <br />
          <strong>Version:</strong> {version}
          <br />
          <strong>Stable policy ID:</strong> breero:
          {title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}:{version}
        </p>
        <div className="mk-legal">
          {children}
          <h2>Questions and policy history</h2>
          <p>
            Contact{" "}
            <a href={`mailto:${legalBusiness.supportEmail}`}>{legalBusiness.supportEmail}</a>.
            Material revisions receive a new version identifier and effective date; prior versions
            are retained in BREERO&apos;s policy change history.
          </p>
          <p>
            Related policies: <Link href="/terms">Terms</Link>, <Link href="/privacy">Privacy</Link>
            , <Link href="/privacy-choices">Privacy choices</Link>,{" "}
            <Link href="/cookies">Cookies</Link>,{" "}
            <Link href="/cookie-preferences">Cookie preferences</Link>, and{" "}
            <Link href="/communications-preferences">Communication preferences</Link>.
          </p>
        </div>
      </div>
    </article>
  );
}

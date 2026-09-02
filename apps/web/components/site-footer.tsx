import { ShieldIcon } from "@breero/ui";
import Link from "next/link";
import { legalAddress, legalBusiness, legalIdentity } from "@/content/legal";
import { breeroDomains, codestraProductNetwork } from "@/content/domains";
import { Logo } from "./brand/Logo";

const groups = [
  {
    title: "Services",
    links: [
      ["All services", "/services"],
      ["Plumbing", "/services/plumbing"],
      ["Electrical", "/services/electrical"],
      ["Cleaning", "/services/cleaning"],
      ["Request service", "/request-service"],
    ],
  },
  {
    title: "Company & support",
    links: [
      ["About", "/about"],
      ["How it works", "/how-it-works"],
      ["Help centre", "/help"],
      ["Contact", "/contact"],
      ["Accessibility", "/accessibility"],
    ],
  },
  {
    title: "Privacy & terms",
    links: [
      ["Privacy", "/privacy"],
      ["Privacy choices", "/privacy-choices"],
      ["Terms", "/terms"],
      ["Cookies", "/cookies"],
      ["SMS terms", "/sms-terms"],
    ],
  },
] as const;

export function SiteFooter() {
  return (
    <footer className="site-footer hz-site-footer">
      <div className="hz-container">
        <div className="footer__inner hz-site-footer__grid">
          <section className="footer__intro hz-site-footer__intro" aria-labelledby="breero-footer-title">
            <Logo light />
            <p className="hz-eyebrow">Codestra product network</p>
            <h2 id="breero-footer-title" className="hz-site-footer__title">Home services, without the hassle.</h2>
            <span className="footer__trust"><ShieldIcon size={18} />Quote required. No online payment is required or collected.</span>
            <p><strong>{legalIdentity}</strong><br />{legalAddress}<br /><a href={`mailto:${legalBusiness.supportEmail}`}>{legalBusiness.supportEmail}</a></p>
            <div className="hz-domain-list" aria-label="Breero domains">
              <a className="hz-domain-chip" href={breeroDomains.public}>breero.com</a>
              <a className="hz-domain-chip" href={breeroDomains.partners}>partners.breero.com</a>
              <a className="hz-domain-chip" href={breeroDomains.operations}>ops.breero.com</a>
              <a className="hz-domain-chip" href={breeroDomains.administration}>admin.breero.com</a>
            </div>
          </section>

          {groups.map((group) => (
            <nav key={group.title} aria-label={`${group.title} links`}>
              <h3 className="hz-site-footer__heading">{group.title}</h3>
              <ul className="hz-site-footer__links">
                {group.links.map(([label, href]) => (
                  <li key={href}><Link className="hz-site-footer__link" href={href}>{label}</Link></li>
                ))}
              </ul>
            </nav>
          ))}
        </div>

        <div className="hz-site-footer__bottom">
          <span>© {new Date().getFullYear()} {legalIdentity}.</span>
          <div className="hz-footer-legal" aria-label="Codestra product network">
            {codestraProductNetwork.map((product) => (
              <a className="hz-site-footer__link" key={product.href} href={product.href}>{product.label}</a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}

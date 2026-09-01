import { ShieldIcon } from "@breero/ui";
import Link from "next/link";
import { legalAddress, legalBusiness, legalIdentity } from "@/content/legal";
import { Logo } from "./brand/Logo";

const groups = [
  {
    title: "Services",
    links: [
      ["All services", "/services"],
      ["Plumbing", "/services/plumbing"],
      ["Electrical", "/services/electrical"],
      ["Cleaning", "/services/cleaning"],
    ],
  },
  {
    title: "Company",
    links: [
      ["About", "/about"],
      ["How it works", "/how-it-works"],
      ["Careers", "/careers"],
      ["Press", "/press"],
    ],
  },
  {
    title: "Support",
    links: [
      ["Request service", "/request-service"],
      ["Help centre", "/help"],
      ["Contact", "/contact"],
      ["Refund, rescheduling & cancellation", "/refund-cancellation"],
      ["Service fulfillment", "/service-fulfillment"],
    ],
  },
  {
    title: "Privacy & communications",
    links: [
      ["Privacy choices", "/privacy-choices"],
      ["Cookie notice", "/cookies"],
      ["Cookie preferences", "/cookie-preferences"],
      ["Communication preferences", "/communications-preferences"],
      ["SMS terms", "/sms-terms"],
    ],
  },
  {
    title: "Professionals",
    links: [
      ["Partner information", "/partners"],
      ["Provider terms", "/provider-terms"],
      ["Lead terms", "/lead-terms"],
      ["Partner interest", "/partners#interest"],
    ],
  },
];

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="footer__inner">
        <div className="footer__intro">
          <Logo light />
          <p>Home services, without the hassle.</p>
          <span className="footer__trust">
            <ShieldIcon size={18} />
            Quote required. No online payment is required or collected.
          </span>
          <p>
            <strong>{legalIdentity}</strong>
            <br />
            {legalAddress}
            <br />
            <a href={`mailto:${legalBusiness.supportEmail}`}>{legalBusiness.supportEmail}</a>
            <br />
            <a href={legalBusiness.corporateSite}>Codestra.co</a>
          </p>
        </div>
        <div className="footer__links">
          {groups.map((group) => (
            <div key={group.title}>
              <h2>{group.title}</h2>
              {group.links.map(([label, href]) => (
                <Link key={href} href={href}>
                  {label}
                </Link>
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className="footer__legal">
        <span>
          © {new Date().getFullYear()} {legalIdentity}.
        </span>
        <div>
          <Link href="/privacy">Privacy</Link>
          <Link href="/privacy-choices">Privacy choices</Link>
          <Link href="/terms">Terms</Link>
          <Link href="/service-fulfillment">Fulfillment</Link>
          <Link href="/cookies">Cookies</Link>
          <Link href="/accessibility">Accessibility</Link>
        </div>
      </div>
    </footer>
  );
}

"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRightIcon, CloseIcon, IconButton, MenuIcon, ShieldIcon, UserIcon } from "@breero/ui";
import { Logo } from "./brand/Logo";
import { navigation } from "@/content/navigation";
import { breeroDomains } from "@/content/domains";

const links = navigation;

export function SiteHeader() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => setOpen(false), [pathname]);

  useEffect(() => {
    if (!open) return;
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", close);
    return () => document.removeEventListener("keydown", close);
  }, [open]);

  return (
    <header className="site-header hz-site-header">
      <div className="site-header__bar hz-container hz-site-header__inner">
        <div className="hz-brand">
          <Logo light priority />
          <span className="hz-brand__domain">breero.com</span>
        </div>

        <nav className="desktop-nav hz-site-nav hz-site-nav--desktop" aria-label="Main navigation">
          {links.map((link) => (
            <Link
              className="hz-site-nav__link"
              key={link.href}
              href={link.href}
              aria-current={pathname === link.href ? "page" : undefined}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="site-header__actions hz-header-actions">
          <Link className="header-signin hz-button hz-button--secondary hz-button--small" href="/account">
            <UserIcon size={18} />
            Sign in
          </Link>
          <Link
            className="br-button br-button--primary br-button--sm header-book hz-button hz-button--primary hz-button--small"
            href="/booking"
            data-cta="header-book"
          >
            Book a service <ArrowRightIcon size={17} />
          </Link>
          <IconButton
            className="mobile-menu-button hz-menu-button"
            label={open ? "Close menu" : "Open menu"}
            aria-expanded={open}
            aria-controls="mobile-navigation"
            onClick={() => setOpen(!open)}
          >
            {open ? <CloseIcon /> : <MenuIcon />}
          </IconButton>
        </div>
      </div>

      <div id="mobile-navigation" className="mobile-nav hz-mobile-panel" data-open={open}>
        <div className="hz-container hz-mobile-panel__inner">
          <nav aria-label="Mobile navigation">
            {links.map((link) => (
              <Link
                className="hz-site-nav__link"
                key={link.href}
                href={link.href}
                aria-current={pathname === link.href ? "page" : undefined}
                onClick={() => setOpen(false)}
              >
                {link.label}<ArrowRightIcon size={18} />
              </Link>
            ))}
            <Link className="hz-site-nav__link" href="/account" onClick={() => setOpen(false)}>
              <UserIcon size={19} />Sign in
            </Link>
            <a className="hz-site-nav__link" href={breeroDomains.partners}>Partner portal</a>
          </nav>
          <Link
            className="br-button br-button--primary br-button--lg br-button--full hz-button hz-button--primary"
            href="/booking"
            onClick={() => setOpen(false)}
            data-cta="mobile-book"
          >
            Book a service <ArrowRightIcon />
          </Link>
          <p><ShieldIcon size={17} />Verified professionals. Clear booking.</p>
        </div>
      </div>
    </header>
  );
}

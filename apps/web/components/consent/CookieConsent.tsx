"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { readConsentChoice, saveConsentChoice } from "@/lib/consent";

export function CookieConsent() {
  const [open, setOpen] = useState(false);
  const [manage, setManage] = useState(false);
  const [analytics, setAnalytics] = useState(false);
  const [advertising, setAdvertising] = useState(false);
  useEffect(() => {
    const saved = readConsentChoice();
    const gpc =
      (navigator as Navigator & { globalPrivacyControl?: boolean }).globalPrivacyControl === true;
    if (gpc && !saved) {
      saveConsentChoice(false, false, "gpc");
      return;
    }
    if (!saved) setOpen(true);
  }, []);
  const save = (analyticsAllowed: boolean, advertisingAllowed: boolean) => {
    saveConsentChoice(analyticsAllowed, advertisingAllowed, "banner");
    setOpen(false);
    setManage(false);
  };
  const reopen = () => {
    const saved = readConsentChoice();
    setAnalytics(saved?.analytics ?? false);
    setAdvertising(saved?.advertising ?? false);
    setManage(true);
    setOpen(true);
  };
  if (!open)
    return (
      <button type="button" className="cookie-settings" onClick={reopen}>
        Cookie preferences
      </button>
    );
  return (
    <section
      className="cookie-consent"
      role="dialog"
      aria-modal="true"
      aria-labelledby="cookie-consent-title"
    >
      <h2 id="cookie-consent-title">Your privacy choices</h2>
      <p>
        BREERO uses necessary browser storage for security and requested site functions. Optional
        analytics and advertising stay off unless you allow them.
      </p>
      {manage && (
        <div className="cookie-consent__choices">
          <label>
            <input
              type="checkbox"
              checked={analytics}
              onChange={(event) => setAnalytics(event.target.checked)}
            />
            <span>
              <strong>Analytics</strong>
              <small>Helps us understand page and booking usage.</small>
            </span>
          </label>
          <label>
            <input
              type="checkbox"
              checked={advertising}
              onChange={(event) => setAdvertising(event.target.checked)}
            />
            <span>
              <strong>Advertising</strong>
              <small>Allows advertising technology only when the service is configured.</small>
            </span>
          </label>
        </div>
      )}
      <div className="cookie-consent__actions">
        <button type="button" onClick={() => save(true, true)}>
          Accept all
        </button>
        <button type="button" onClick={() => save(false, false)}>
          Reject nonessential
        </button>
        {manage ? (
          <button type="button" onClick={() => save(analytics, advertising)}>
            Save selection
          </button>
        ) : (
          <button type="button" onClick={() => setManage(true)}>
            Manage preferences
          </button>
        )}
      </div>
      <p className="cookie-consent__links">
        <Link href="/cookies">Cookie policy</Link> ·{" "}
        <Link href="/cookie-preferences">Full preferences</Link>
      </p>
    </section>
  );
}

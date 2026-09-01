"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { readConsentChoice, saveConsentChoice } from "@/lib/consent";
export function CookiePreferences() {
  const [analytics, setAnalytics] = useState(false);
  const [advertising, setAdvertising] = useState(false);
  const [savedMessage, setSavedMessage] = useState(false);
  useEffect(() => {
    const saved = readConsentChoice();
    setAnalytics(saved?.analytics ?? false);
    setAdvertising(saved?.advertising ?? false);
  }, []);
  const save = () => {
    saveConsentChoice(analytics, advertising);
    setSavedMessage(true);
  };
  return (
    <article className="mk-section">
      <div className="mk-container mk-narrow">
        <p className="mk-eyebrow">BREERO policy</p>
        <h1>Cookie preferences</h1>
        <p>
          Necessary storage supports security, consent and requested site functions and cannot be
          disabled here. Optional purposes can be changed or withdrawn at any time.
        </p>
        <div className="cookie-preferences">
          <label>
            <input
              type="checkbox"
              checked={analytics}
              onChange={(event) => {
                setAnalytics(event.target.checked);
                setSavedMessage(false);
              }}
            />
            <span>
              <strong>Optional analytics</strong>
              <small>Measure page and booking usage without enabling advertising.</small>
            </span>
          </label>
          <label>
            <input
              type="checkbox"
              checked={advertising}
              onChange={(event) => {
                setAdvertising(event.target.checked);
                setSavedMessage(false);
              }}
            />
            <span>
              <strong>Optional advertising</strong>
              <small>Permit configured advertising technology and related storage.</small>
            </span>
          </label>
          <button type="button" onClick={save}>
            Save preferences
          </button>
          <p aria-live="polite">{savedMessage ? "Your cookie preferences have been saved." : ""}</p>
        </div>
        <p>
          Read the <Link href="/cookies">Cookie Policy</Link> or{" "}
          <Link href="/privacy">Privacy Policy</Link>.
        </p>
      </div>
    </article>
  );
}

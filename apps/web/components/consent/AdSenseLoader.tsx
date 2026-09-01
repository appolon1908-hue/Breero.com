"use client";
import { useEffect } from "react";
import { adsenseClientId, adsenseConfigured } from "@/lib/adsense";
import { CONSENT_UPDATED_EVENT, readConsentChoice } from "@/lib/consent";
const SCRIPT_ID = "breero-adsense-script";
export function AdSenseLoader() {
  useEffect(() => {
    const sync = () => {
      if (!adsenseConfigured || !readConsentChoice()?.advertising) {
        document.getElementById(SCRIPT_ID)?.remove();
        return;
      }
      if (document.getElementById(SCRIPT_ID)) return;
      const script = document.createElement("script");
      script.id = SCRIPT_ID;
      script.async = true;
      script.crossOrigin = "anonymous";
      script.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${encodeURIComponent(adsenseClientId)}`;
      document.head.appendChild(script);
    };
    sync();
    window.addEventListener(CONSENT_UPDATED_EVENT, sync);
    return () => window.removeEventListener(CONSENT_UPDATED_EVENT, sync);
  }, []);
  return null;
}

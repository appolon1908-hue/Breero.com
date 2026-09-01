export const CONSENT_STORAGE_KEY = "breero_cookie_preferences_v1";
export const CONSENT_UPDATED_EVENT = "breero:consent-updated";

const OPTIONAL_ANALYTICS_KEYS = ["breero_attribution_v1", "breero_anonymous_session_id"] as const;

export type ConsentSource = "banner" | "gpc" | "preferences";
export type ConsentChoice = {
  analytics: boolean;
  advertising: boolean;
  updatedAt: string;
  source: ConsentSource;
};

const storage = (): Storage | null => {
  try {
    return typeof window === "undefined" ? null : window.localStorage;
  } catch {
    return null;
  }
};

export function readConsentChoice(): ConsentChoice | null {
  try {
    const value = JSON.parse(
      storage()?.getItem(CONSENT_STORAGE_KEY) ?? "null",
    ) as Partial<ConsentChoice> | null;
    if (!value || typeof value !== "object" || typeof value.analytics !== "boolean") return null;
    return {
      analytics: value.analytics,
      advertising: value.advertising === true,
      updatedAt: typeof value.updatedAt === "string" ? value.updatedAt : "",
      source: value.source === "banner" || value.source === "gpc" ? value.source : "preferences",
    };
  } catch {
    return null;
  }
}

export function saveConsentChoice(
  analytics: boolean,
  advertising = false,
  source: ConsentSource = "preferences",
): ConsentChoice {
  const choice: ConsentChoice = {
    analytics,
    advertising,
    updatedAt: new Date().toISOString(),
    source,
  };
  const browserStorage = storage();
  try {
    browserStorage?.setItem(CONSENT_STORAGE_KEY, JSON.stringify(choice));
    if (!analytics) OPTIONAL_ANALYTICS_KEYS.forEach((key) => browserStorage?.removeItem(key));
  } catch {
    /* Optional processing remains off when browser storage is unavailable. */
  }
  if (typeof window !== "undefined")
    window.dispatchEvent(new CustomEvent<ConsentChoice>(CONSENT_UPDATED_EVENT, { detail: choice }));
  return choice;
}

export function analyticsConsentGranted(): boolean {
  return readConsentChoice()?.analytics === true;
}

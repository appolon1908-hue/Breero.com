const ADSENSE_CLIENT_PATTERN = /^ca-pub-\d{16}$/;
export const adsenseClientId = (process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID ?? "").trim();
export const adsenseConfigured =
  process.env.NEXT_PUBLIC_ADSENSE_ENABLED === "true" &&
  ADSENSE_CLIENT_PATTERN.test(adsenseClientId);
export const isValidAdsenseClientId = (value: string): boolean =>
  ADSENSE_CLIENT_PATTERN.test(value);

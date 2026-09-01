import type { MetadataRoute } from "next";
export default function robots(): MetadataRoute.Robots {
  const staging =
    process.env.APP_ENV === "staging" || process.env.NEXT_PUBLIC_APP_ENV === "staging";
  return staging
    ? { rules: { userAgent: "*", disallow: "/" } }
    : {
        rules: { userAgent: "*", allow: "/", disallow: ["/account/", "/booking/"] },
        sitemap: `${process.env.NEXT_PUBLIC_APP_URL ?? "https://breero.com"}/sitemap.xml`,
      };
}

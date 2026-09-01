import type { MetadataRoute } from "next";
import publicRoutes from "@/content/public-routes.json";
export default function sitemap(): MetadataRoute.Sitemap {
  const base = process.env.NEXT_PUBLIC_APP_URL ?? "https://breero.com";
  return publicRoutes
    .filter((path) => path !== "/book")
    .map((path) => ({
      url: `${base}${path === "/" ? "" : path}`,
      changeFrequency: path.startsWith("/services") ? "weekly" : "monthly",
      priority: path === "/" ? 1 : path === "/services" ? 0.9 : 0.6,
    }));
}

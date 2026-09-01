import type { Metadata } from "next";
import { CookiePreferences } from "./preferences";
export const metadata: Metadata = {
  title: "Cookie preferences",
  description: "Manage optional BREERO browser storage.",
};
export default function Page() {
  return <CookiePreferences />;
}

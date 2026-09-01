import type { Metadata } from "next";
import { StandardPage } from "@/components/marketing/StandardPage";
import { corePages } from "@/content/pages/core";
export const metadata: Metadata = {
  title: "Service areas",
  description: corePages.locations.description,
  alternates: { canonical: "/locations" },
};
export default function Page() {
  return <StandardPage content={corePages.locations} />;
}

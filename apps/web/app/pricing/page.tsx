import type { Metadata } from "next";
import { StandardPage } from "@/components/marketing/StandardPage";
import { corePages } from "@/content/pages/core";
export const metadata: Metadata = {
  title: "Pricing explained",
  description: corePages.pricing.description,
  alternates: { canonical: "/pricing" },
};
export default function Page() {
  return <StandardPage content={corePages.pricing} />;
}

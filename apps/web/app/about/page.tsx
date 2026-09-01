import type { Metadata } from "next";
import { StandardPage } from "@/components/marketing/StandardPage";
import { corePages } from "@/content/pages/core";
export const metadata: Metadata = {
  title: "About BREERO",
  description: corePages.about.description,
  alternates: { canonical: "/about" },
};
export default function Page() {
  return <StandardPage content={corePages.about} />;
}

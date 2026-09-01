import type { Metadata } from "next";
import { StandardPage } from "@/components/marketing/StandardPage";
import { HowItWorks } from "@/components/marketing/HowItWorks";
import { corePages } from "@/content/pages/core";
export const metadata: Metadata = {
  title: "How BREERO works",
  description: corePages["how-it-works"].description,
  alternates: { canonical: "/how-it-works" },
};
export default function Page() {
  return (
    <StandardPage content={corePages["how-it-works"]}>
      <HowItWorks />
    </StandardPage>
  );
}

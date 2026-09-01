import type { Metadata } from "next";
import { StandardPage } from "@/components/marketing/StandardPage";
import { WhyBreero } from "@/components/marketing/WhyBreero";
import { corePages } from "@/content/pages/core";
export const metadata: Metadata = {
  title: "Why BREERO",
  description: corePages["why-breero"].description,
  alternates: { canonical: "/why-breero" },
};
export default function Page() {
  return (
    <StandardPage content={corePages["why-breero"]}>
      <WhyBreero />
    </StandardPage>
  );
}

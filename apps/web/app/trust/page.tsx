import type { Metadata } from "next";
import { StandardPage } from "@/components/marketing/StandardPage";
import { TrustBar } from "@/components/marketing/TrustBar";
import { corePages } from "@/content/pages/core";
export const metadata: Metadata = {
  title: "Trust and safety",
  description: corePages.trust.description,
  alternates: { canonical: "/trust" },
};
export default function Page() {
  return (
    <StandardPage content={corePages.trust}>
      <TrustBar />
    </StandardPage>
  );
}

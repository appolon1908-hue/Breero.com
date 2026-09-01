import type { Metadata } from "next";
import { StandardPage } from "@/components/marketing/StandardPage";
import { corePages } from "@/content/pages/core";
export const metadata: Metadata = {
  title: "Service standards",
  description: corePages["service-guarantee"].description,
  alternates: { canonical: "/service-guarantee" },
};
export default function Page() {
  return <StandardPage content={corePages["service-guarantee"]} />;
}

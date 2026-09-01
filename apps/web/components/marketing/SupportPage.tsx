import type { Metadata } from "next";
import { StandardPage } from "./StandardPage";
import { supportPages } from "@/content/pages/support";
export const supportMetadata = (slug: string): Metadata => ({
  title: supportPages[slug].title,
  description: supportPages[slug].description,
  alternates: { canonical: `/${slug}` },
});
export function SupportPage({ slug }: { slug: string }) {
  return <StandardPage content={supportPages[slug]} />;
}

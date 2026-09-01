import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { campaigns } from "@/content/campaigns";
import { Hero } from "@/components/marketing/Hero";
import { ServiceGrid } from "@/components/marketing/ServiceGrid";
import { CTASection } from "@/components/marketing/CTASection";
import { images } from "@/content/images";

export function generateStaticParams() {
  return campaigns
    .filter((campaign) => campaign.published)
    .map((campaign) => ({ slug: campaign.slug }));
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const campaign = campaigns.find((item) => item.slug === slug && item.published);
  return campaign
    ? {
        title: campaign.title,
        description: campaign.headline,
        alternates: { canonical: `/landing/${campaign.slug}` },
      }
    : { title: "Campaign not available", robots: { index: false } };
}
export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const campaign = campaigns.find((item) => item.slug === slug && item.published);
  if (!campaign) notFound();
  return (
    <>
      <Hero
        compact
        eyebrow="BREERO home care"
        title={campaign.headline}
        description="Practical service categories, clear booking and trusted support for your home."
        image={images.homeHero}
      />
      <section className="mk-section">
        <div className="mk-container">
          <header className="mk-heading">
            <h2>Services for the season.</h2>
          </header>
          <ServiceGrid />
        </div>
      </section>
      <CTASection />
    </>
  );
}

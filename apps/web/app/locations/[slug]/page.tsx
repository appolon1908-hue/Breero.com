import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { locations } from "@/content/locations";
import { Hero } from "@/components/marketing/Hero";
import { ServiceGrid } from "@/components/marketing/ServiceGrid";
import { CTASection } from "@/components/marketing/CTASection";
import { images } from "@/content/images";

export function generateStaticParams() {
  return locations
    .filter((location) => location.published)
    .map((location) => ({ slug: location.slug }));
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const location = locations.find((item) => item.slug === slug && item.published);
  return location
    ? {
        title: `Home services in ${location.name}`,
        description: location.description,
        alternates: { canonical: `/locations/${location.slug}` },
      }
    : { title: "Location not available", robots: { index: false } };
}
export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const location = locations.find((item) => item.slug === slug && item.published);
  if (!location) notFound();
  return (
    <>
      <Hero
        compact
        eyebrow="Local home services"
        title={`Home services in ${location.name}.`}
        description={location.description}
        image={images.homeHero}
      />
      <section className="mk-section">
        <div className="mk-container">
          <header className="mk-heading">
            <p className="mk-eyebrow">Available categories</p>
            <h2>Help for the jobs around your home.</h2>
            <p>
              Exact serviceability and availability are still checked securely for your address.
            </p>
          </header>
          <ServiceGrid limit={6} />
        </div>
      </section>
      <CTASection />
    </>
  );
}

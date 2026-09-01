import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { marketingServiceBySlug, marketingServices } from "@/content/services";
import { ServicePageTemplate } from "@/components/marketing/ServicePageTemplate";
export function generateStaticParams() {
  return marketingServices.map((service) => ({ slug: service.slug }));
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const service = marketingServiceBySlug((await params).slug);
  return service
    ? {
        title: `${service.name} services`,
        description: service.description,
        alternates: { canonical: `/services/${service.slug}` },
        openGraph: {
          title: `${service.name} services | BREERO`,
          description: service.description,
          images: [service.image.src],
        },
      }
    : { title: "Service not found" };
}
export default async function ServicePage({ params }: { params: Promise<{ slug: string }> }) {
  const service = marketingServiceBySlug((await params).slug);
  if (!service) notFound();
  return <ServicePageTemplate service={service} />;
}

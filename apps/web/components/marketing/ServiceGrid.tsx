import { marketingServices } from "@/content/services";
import { ServiceCard } from "./ServiceCard";
export function ServiceGrid({ limit }: { limit?: number }) {
  return (
    <div className="mk-service-grid">
      {marketingServices.slice(0, limit).map((service) => (
        <ServiceCard key={service.slug} service={service} />
      ))}
    </div>
  );
}

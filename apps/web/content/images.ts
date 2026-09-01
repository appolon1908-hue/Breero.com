const image = (src: string, alt: string) => ({ src, alt });
export const images = {
  homeHero: image(
    "/images/hero/home-hero.webp",
    "A home-service professional arriving at a bright residential home",
  ),
  servicesHero: image(
    "/images/hero/services-hero.webp",
    "A friendly professional welcomed at a customer's home",
  ),
  bookingHero: image(
    "/images/hero/booking-hero.webp",
    "A professional arriving for a scheduled home-service visit",
  ),
  trustHero: image(
    "/images/hero/trust-hero.webp",
    "Home-service professionals preparing for their day",
  ),
  partnerHero: image(
    "/images/hero/partner-hero.webp",
    "Two local service professionals reviewing their schedule",
  ),
  aboutHero: image("/images/hero/about-hero.webp", "A helpful professional greeting a homeowner"),
  plumbing: image(
    "/images/services/plumbing.webp",
    "A plumbing professional inspecting pipework beneath a kitchen sink",
  ),
  electrical: image(
    "/images/services/electrical.webp",
    "An electrical professional safely checking a wall outlet",
  ),
  handyman: image(
    "/images/services/handyman.webp",
    "A home professional preparing for a local service visit",
  ),
  heating: image(
    "/images/services/heating.webp",
    "A heating professional checking a home installation",
  ),
  cooling: image(
    "/images/services/cooling.webp",
    "A cooling specialist carrying out a careful home inspection",
  ),
  applianceRepair: image(
    "/images/services/appliance-repair.webp",
    "A technician diagnosing a household appliance",
  ),
  cleaning: image(
    "/images/services/cleaning.webp",
    "A professional cleaner finishing a bright living room",
  ),
  locksmith: image(
    "/images/services/locksmith.webp",
    "A local professional preparing tools for a home visit",
  ),
  painting: image(
    "/images/services/painting.webp",
    "A professional working carefully in a clean modern home",
  ),
  carpentry: image(
    "/images/services/carpentry.webp",
    "A skilled professional preparing for a home project",
  ),
  movingHelp: image(
    "/images/services/moving-help.webp",
    "Local professionals ready to help with a home move",
  ),
  homeMaintenance: image(
    "/images/services/home-maintenance.webp",
    "A professional maintaining a bright family home",
  ),
  happyHomeowner: image(
    "/images/lifestyle/happy-homeowner.webp",
    "A homeowner welcoming professional help",
  ),
  technicianArrival: image(
    "/images/lifestyle/technician-arrival.webp",
    "A professional arriving for a home visit",
  ),
  technicianWorking: image(
    "/images/lifestyle/technician-working.webp",
    "A professional working carefully in a home",
  ),
  familyHome: image("/images/lifestyle/family-home.webp", "A bright attainable family home"),
  cleanModernHome: image("/images/lifestyle/clean-modern-home.webp", "A clean modern living space"),
  bookingOnPhone: image(
    "/images/lifestyle/booking-on-phone.webp",
    "A homeowner arranging a service visit",
  ),
  verifiedProfessional: image(
    "/images/trust/verified-professional.webp",
    "A verified home-service professional",
  ),
  qualityCheck: image("/images/trust/quality-check.webp", "A careful professional quality check"),
  supportTeam: image(
    "/images/trust/support-team.webp",
    "Professionals coordinating customer support",
  ),
  serviceGuarantee: image(
    "/images/trust/service-guarantee.webp",
    "A professional completing a careful handover",
  ),
  breeroTeam: image(
    "/images/about/breero-team.webp",
    "Home-service professionals working together",
  ),
  partnerProfessional: image(
    "/images/partners/partner-professional.webp",
    "Two service professionals reviewing work",
  ),
  serviceVan: image(
    "/images/partners/service-van.webp",
    "Professionals beside a clean service vehicle",
  ),
  localCommunity: image(
    "/images/about/local-community.webp",
    "A welcoming local residential community",
  ),
} as const;

import { images } from "../images";
import type { StandardPageContent } from "@/components/marketing/StandardPage";
const support = (
  eyebrow: string,
  title: string,
  description: string,
  sections: StandardPageContent["sections"],
  image = images.aboutHero,
): StandardPageContent => ({ eyebrow, title, description, sections, image });
export const supportPages: Record<string, StandardPageContent> = {
  help: support(
    "Help centre",
    "Help for your BREERO journey.",
    "Find clear guidance for booking, payment, service status and account access.",
    [
      {
        title: "Booking and scheduling",
        text: "Understand services, address checks, live availability, booking status and appointment changes.",
      },
      {
        title: "Independent providers",
        text: "BREERO coordinates the marketplace journey; the selected provider remains responsible for the underlying service, final estimate and workmanship unless BREERO expressly states otherwise.",
      },
      {
        title: "Cancellations, refunds and service issues",
        text: "Review the linked policies for timing and eligibility. Contact support promptly when a service or payment needs individual review.",
      },
      {
        title: "Account, payment and support",
        text: "Use the account experience for status and access controls. If the guidance does not solve it, contact support@breero.com.",
      },
    ],
  ),
  faq: support(
    "Frequently asked questions",
    "Straight answers to common questions.",
    "Booking and home services should not require decoding fine print.",
    [
      {
        title: "Booking",
        text: "Choose a service, answer relevant questions, validate your address and pick an available time.",
      },
      {
        title: "Payments",
        text: "Review authoritative amount and currency before secure payment.",
      },
      { title: "Professionals", text: "BREERO checks relevant marketplace partner information." },
      { title: "Support", text: "Use the contact page if your question needs individual help." },
    ],
  ),
  reviews: support(
    "Customer feedback",
    "Verified stories will live here.",
    "BREERO does not publish invented ratings or testimonials. This page is ready for approved, verified customer feedback.",
    [
      {
        title: "Verification first",
        text: "Only approved feedback linked to a genuine service should be presented as verified.",
      },
      {
        title: "No inflated metrics",
        text: "Aggregate ratings remain hidden until the source and sample are trustworthy.",
      },
      {
        title: "Useful context",
        text: "Future reviews can include service and city when consent permits.",
      },
      {
        title: "Share feedback",
        text: "Customer feedback workflows will be linked when formally available.",
      },
    ],
    images.qualityCheck,
  ),
  emergency: support(
    "Urgent help",
    "Know when BREERO is not the first call.",
    "BREERO is a booking marketplace, not an emergency response service.",
    [
      {
        title: "Immediate danger",
        text: "Contact local emergency services when people, property or public safety are at immediate risk.",
      },
      {
        title: "Gas or electrical danger",
        text: "Move away from danger and use the appropriate local emergency utility or public service.",
      },
      {
        title: "Water damage",
        text: "If safe, isolate the water supply before seeking urgent professional help.",
      },
      {
        title: "Bookable work",
        text: "For non-emergency service, check current catalog availability through booking.",
      },
    ],
    images.trustHero,
  ),
  "home-care": support(
    "Home care guidance",
    "Small habits. Fewer surprises.",
    "Practical guidance for maintaining a comfortable home without exaggerated promises.",
    [
      {
        title: "Seasonal checks",
        text: "Review heating, cooling, seals and drainage before weather changes.",
      },
      {
        title: "Act on warning signs",
        text: "Leaks, unusual smells, repeated faults and electrical heat deserve timely attention.",
      },
      {
        title: "Keep useful records",
        text: "Service dates, appliance details and photos can make future diagnosis clearer.",
      },
      {
        title: "Know your limits",
        text: "Use a qualified professional when work involves regulated or hazardous systems.",
      },
    ],
    images.homeMaintenance,
  ),
  careers: support(
    "Careers",
    "Help build a better home-services experience.",
    "BREERO career opportunities will be published here when approved roles are open.",
    [
      {
        title: "No ghost roles",
        text: "We do not advertise positions that are not genuinely open.",
      },
      {
        title: "Inclusive process",
        text: "Future role descriptions will explain expectations and selection clearly.",
      },
      {
        title: "Stay informed",
        text: "Approved opportunities can be announced through official BREERO channels.",
      },
      {
        title: "Supplier enquiries",
        text: "Use the contact page rather than submitting personal employment data.",
      },
    ],
    images.partnerProfessional,
  ),
  press: support(
    "Press and media",
    "BREERO facts, without the hype.",
    "Approved company information and media contacts will be published here.",
    [
      {
        title: "Brand assets",
        text: "Use only the logo variants and guidance in the central brand system.",
      },
      { title: "Company facts", text: "Metrics remain unpublished until verified and approved." },
      {
        title: "Media enquiries",
        text: "Contact support@breero.com with your publication and deadline.",
      },
      {
        title: "Announcements",
        text: "Only approved releases should appear as company statements.",
      },
    ],
    images.aboutHero,
  ),
  blog: support(
    "Home care journal",
    "Useful advice for real homes.",
    "The editorial architecture is ready; articles remain unpublished until reviewed for accuracy and ownership.",
    [
      {
        title: "Practical over promotional",
        text: "Articles should help homeowners make better decisions.",
      },
      {
        title: "Qualified review",
        text: "Safety-sensitive technical advice requires an appropriate reviewer.",
      },
      { title: "Original content", text: "No keyword stuffing or recycled generic copy." },
      {
        title: "Local accuracy",
        text: "Regulatory or regional claims must match the market served.",
      },
    ],
    images.homeMaintenance,
  ),
  availability: support(
    "Availability",
    "The right time depends on the service and address.",
    "BREERO checks live capacity inside the canonical booking flow.",
    [
      {
        title: "Address first",
        text: "Coverage and legal entity are resolved securely by the platform.",
      },
      {
        title: "Live slots",
        text: "Displayed times reflect current service capacity when requested.",
      },
      {
        title: "Stale slots",
        text: "A slot can change before booking; the backend confirms capacity safely.",
      },
      {
        title: "No promises here",
        text: "This information page never invents appointment availability.",
      },
    ],
    images.bookingHero,
  ),
};

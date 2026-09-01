import { images } from "../images";
import type { StandardPageContent } from "@/components/marketing/StandardPage";
export const corePages: Record<string, StandardPageContent> = {
  "how-it-works": {
    eyebrow: "A simpler service journey",
    title: "From home problem to handled.",
    description:
      "Breero.com helps customers connect and coordinate with independent service providers across supported categories and service areas.",
    image: images.bookingHero,
    sections: [
      {
        title: "Tell us what you need",
        text: "Share the service category, location, timing and relevant details needed to evaluate and coordinate your request.",
      },
      {
        title: "Breero coordinates the opportunity",
        text: "Breero may use service type, location, availability, provider eligibility and other relevant factors to identify potentially suitable independent providers.",
      },
      {
        title: "Provider estimate and scope",
        text: "Unless expressly stated otherwise for a specific offering, the independent provider determines whether it can perform the work and communicates the proposed scope, availability and price.",
      },
      {
        title: "You decide",
        text: "A lead, match, appointment or estimate request does not require you to purchase the underlying service. When you and a provider agree to proceed, the provider is responsible for performing the agreed work.",
      },
    ],
  },
  "why-breero": {
    eyebrow: "Why BREERO",
    title: "Confidence built into every step.",
    description:
      "A service coordination and lead-generation marketplace designed around clear requests, provider matching and practical support.",
    image: images.qualityCheck,
    sections: [
      {
        title: "Less chasing",
        text: "One guided path replaces scattered calls and repeated explanations.",
      },
      {
        title: "Clear decisions",
        text: "Customers remain free to accept or reject a provider proposal.",
      },
      {
        title: "Independent professionals",
        text: "Providers remain responsible for their own licensing, permits, insurance, estimates, pricing, workmanship and legal compliance where applicable.",
      },
      {
        title: "Support paths",
        text: "Breero may help with communications, scheduling, follow-up and dispute intake without becoming the underlying contractor merely because the request originated on the platform.",
      },
    ],
  },
  pricing: {
    eyebrow: "Pricing explained",
    title: "Clear before you commit.",
    description:
      "Unless a particular Breero offering expressly states otherwise, the independent provider establishes the proposed scope and price for the underlying service.",
    image: images.bookingHero,
    sections: [
      {
        title: "Provider pricing",
        text: "The provider evaluates the requested work and communicates the estimate, scope and applicable service terms.",
      },
      {
        title: "Platform charges",
        text: "Any Breero fee, paid lead price or other platform charge must be disclosed before the applicable purchase or acceptance.",
      },
      {
        title: "Additional work",
        text: "Work outside an agreed scope should be separately disclosed and approved between the customer and provider.",
      },
      {
        title: "Refund questions",
        text: "Breero refund and lead-dispute rules are described in the applicable policy pages and do not waive rights that cannot legally be waived.",
      },
    ],
  },
  trust: {
    eyebrow: "Trust and safety",
    title: "Your home deserves careful standards.",
    description:
      "Breero combines marketplace requirements, clear customer disclosures and support while independent providers remain responsible for the underlying services they agree to perform.",
    image: images.trustHero,
    sections: [
      {
        title: "Marketplace standards",
        text: "Breero may establish provider eligibility, documentation, conduct, quality and lead-handling requirements.",
      },
      {
        title: "Independent responsibility",
        text: "Providers remain responsible for qualifications, licensing, permits, insurance, estimates, pricing, scope, materials, workmanship and safety applicable to their work.",
      },
      {
        title: "Privacy by design",
        text: "Customer information needed to coordinate a request may be shared with potentially suitable providers and authorized service partners as described in the Privacy Policy.",
      },
      {
        title: "Clear support",
        text: "Customer and provider questions can be sent to support@breero.com.",
      },
    ],
  },
  "service-guarantee": {
    eyebrow: "Service standards",
    title: "Clear expectations from request to follow-up.",
    description:
      "Breero sets marketplace and communication expectations without representing that every independent provider service is performed or warranted by Codestra LLC.",
    image: images.trustHero,
    sections: [
      {
        title: "What Breero supports",
        text: "Request intake, matching, scheduling, communications, notifications, lead management and follow-up may be facilitated through the platform.",
      },
      {
        title: "What providers control",
        text: "Unless expressly stated otherwise, providers determine whether they can perform the request and establish their estimate, scope, pricing, scheduling commitments and warranties.",
      },
      {
        title: "When plans change",
        text: "Breero may help facilitate rescheduling, cancellation communications and dispute intake.",
      },
      {
        title: "Rights preserved",
        text: "Nothing in Breero policy is intended to exclude or waive rights, remedies or obligations that cannot lawfully be excluded or waived.",
      },
    ],
  },
  about: {
    eyebrow: "About BREERO",
    title: "A better way to coordinate everyday services.",
    description:
      "BREERO is a service-coordination and lead-generation platform operated by Codestra LLC.",
    image: images.aboutHero,
    sections: [
      {
        title: "Our role",
        text: "BREERO connects customers seeking services with independent service providers across supported service categories and geographic areas.",
      },
      {
        title: "Independent providers",
        text: "Unless expressly stated otherwise for a specific offering, Codestra LLC and BREERO do not perform the underlying contractor, repair, maintenance, cleaning, hauling, installation or other professional services requested through the platform.",
      },
      {
        title: "Corporate operator",
        text: "BREERO is operated by Codestra LLC. Corporate information is available at Codestra.co.",
      },
      {
        title: "Business address",
        text: "20633 Longenbaugh Rd, Cypress, TX 77433, United States.",
      },
    ],
  },
  contact: {
    eyebrow: "Contact BREERO",
    title: "How can we help?",
    description:
      "Contact BREERO for customer support, provider questions, policy questions or business enquiries.",
    image: images.aboutHero,
    sections: [
      {
        title: "Customer support",
        text: "Email support@breero.com for service-request, scheduling, cancellation, refund or support questions. Do not send passwords, tokens or payment credentials.",
      },
      {
        title: "Provider support",
        text: "Service professionals can use support@breero.com for lead-policy, account or marketplace questions.",
      },
      {
        title: "Business identity",
        text: "BREERO, operated by Codestra LLC — 20633 Longenbaugh Rd, Cypress, TX 77433, United States. Corporate website: Codestra.co.",
      },
      {
        title: "Urgent safety",
        text: "For immediate danger or emergencies, contact local emergency services first.",
      },
    ],
  },
  partners: {
    eyebrow: "For service professionals",
    title: "Build trust. Do great work.",
    description:
      "Learn how participation in the Breero marketplace is intended to work. Providers remain independent businesses unless a separate written agreement expressly establishes otherwise.",
    image: images.partnerHero,
    sections: [
      {
        title: "Lead opportunities",
        text: "A paid Breero lead is access to a customer opportunity—not a guaranteed job, sale, contract, appointment outcome or revenue amount.",
      },
      {
        title: "Independent responsibility",
        text: "Providers remain responsible for licensing, permits, insurance, qualifications, pricing, taxes, scope, materials, workmanship, warranties, safety and legal compliance applicable to their work.",
      },
      {
        title: "Lead disputes",
        text: "Providers seeking review of a paid lead should submit the dispute within 72 hours of receiving the lead, subject to applicable law and program-specific terms.",
      },
      {
        title: "Register interest",
        text: "Email support@breero.com. A dedicated partner application will be linked only when it is real and accepted.",
      },
    ],
  },
  locations: {
    eyebrow: "Service areas",
    title: "Coverage is checked request by request.",
    description:
      "Breero does not claim serviceability where independent provider coverage has not been operationally supported.",
    image: images.homeHero,
    sections: [
      {
        title: "Why exact locations matter",
        text: "Provider availability can depend on service type, geography, workload, eligibility and scheduling.",
      },
      {
        title: "How matching works",
        text: "Breero may use customer-supplied location and service information to identify potentially suitable independent providers.",
      },
      {
        title: "No automatic contract",
        text: "Submitting a request does not necessarily create a contract for the underlying service with Codestra LLC or Breero.",
      },
      {
        title: "Growing carefully",
        text: "New location pages will appear only after operational approval.",
      },
    ],
  },
};

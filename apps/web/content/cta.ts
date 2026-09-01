export const ctas = {
  bookService: { label: "Book a service", href: "/booking", analytics: "book-service" },
  exploreServices: { label: "Explore services", href: "/services", analytics: "explore-services" },
  partnerInterest: {
    label: "Become a BREERO partner",
    href: "/partners#interest",
    analytics: "partner-interest",
  },
  checkAvailability: {
    label: "Check availability",
    href: "/booking",
    analytics: "check-availability",
  },
} as const;

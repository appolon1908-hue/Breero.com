import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { marketingServices } from "@/content/services";
import { FAQ } from "./FAQ";
import { Hero } from "./Hero";
import { PublicIntakeForm } from "./PublicIntakeForm";
import { ServiceCard } from "./ServiceCard";

describe("marketing system", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("uses the canonical booking CTA", () => {
    render(
      <Hero
        title="Home services"
        description="Trusted help"
        image={{ src: "/images/hero/home-hero.webp", alt: "Professional arriving" }}
      />,
    );
    expect(screen.getByRole("link", { name: "Book a service" })).toHaveAttribute(
      "href",
      "/booking",
    );
  });

  it("links service cards to public service pages", () => {
    render(<ServiceCard service={marketingServices[0]} />);
    expect(screen.getByRole("link")).toHaveAttribute("href", "/services/plumbing");
  });

  it("renders accessible FAQ controls", () => {
    render(<FAQ limit={2} />);
    expect(screen.getAllByText(/How|pricing/i).length).toBeGreaterThan(0);
  });

  it("labels preferred timing as a request when instant booking is disabled", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          new Response(
            JSON.stringify(
              url.includes("capabilities")
                ? {
                    request_intake: true,
                    instant_booking: false,
                    online_payments: false,
                    automatic_assignment: false,
                    provider_self_service: false,
                    marketplace_matching: false,
                    messaging: false,
                    reviews: false,
                  }
                : [{ id: "service-1", slug: "plumbing", name: "Plumbing", is_active: true }],
            ),
            { status: 200 },
          ),
        ),
      ),
    );

    render(<PublicIntakeForm kind="service" />);

    await waitFor(() =>
      expect(screen.getByLabelText("Preferred date (request only)")).toBeEnabled(),
    );
    expect(screen.getByRole("button", { name: "Send request" })).toBeEnabled();
  });

  it("keeps timing request-only when instant booking is enabled", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          new Response(
            JSON.stringify(
              url.includes("capabilities")
                ? {
                    request_intake: true,
                    instant_booking: true,
                    online_payments: false,
                    automatic_assignment: false,
                    provider_self_service: false,
                    marketplace_matching: false,
                    messaging: false,
                    reviews: false,
                  }
                : [{ id: "service-1", slug: "plumbing", name: "Plumbing", is_active: true }],
            ),
            { status: 200 },
          ),
        ),
      ),
    );

    render(<PublicIntakeForm kind="service" />);

    await waitFor(() =>
      expect(screen.getByLabelText("Preferred date (request only)")).toBeEnabled(),
    );
    expect(screen.getByLabelText("Preferred local time (request only)")).toBeEnabled();
    expect(screen.queryByLabelText("Appointment date")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Appointment time")).not.toBeInTheDocument();
  });
});

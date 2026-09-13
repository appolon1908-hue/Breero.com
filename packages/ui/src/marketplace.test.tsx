import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import {
  CapacitySignal,
  MarketplaceServiceCard,
  MarketplaceStatePanel,
  PricingModeBadge,
  ProjectStatusTimeline,
  ProviderTrustCard,
} from "./marketplace";

afterEach(cleanup);

describe("marketplace UI", () => {
  it("labels the three supported pricing modes truthfully", () => {
    const { rerender } = render(<PricingModeBadge mode="instant_bookable" />);
    expect(screen.getByText("Instant booking")).toBeInTheDocument();
    rerender(<PricingModeBadge mode="quote_required" />);
    expect(screen.getByText("Quote required")).toBeInTheDocument();
    rerender(<PricingModeBadge mode="request_only" />);
    expect(screen.getByText("Request only")).toBeInTheDocument();
  });

  it("renders service discovery facts and a real destination", () => {
    render(
      <MarketplaceServiceCard
        title="Electrical inspection"
        description="Request an assessment from an eligible service professional."
        href="/services/electrical-inspection"
        category="Electrical"
        pricingMode="quote_required"
        durationLabel="60–90 minutes"
        coverageLabel="Selected service zones"
        emergencyEligible
      />,
    );

    expect(screen.getByRole("heading", { name: "Electrical inspection" })).toBeInTheDocument();
    expect(screen.getByText("Quote required")).toBeInTheDocument();
    expect(screen.getByText("Emergency eligible")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /view service/i })).toHaveAttribute("href", "/services/electrical-inspection");
  });

  it("does not invent ratings when review evidence is absent", () => {
    render(
      <ProviderTrustCard
        providerName="Example Home Services"
        trust={[{ kind: "business", status: "verified" }, { kind: "insurance", status: "pending" }]}
      />,
    );

    expect(screen.getByRole("heading", { name: "Example Home Services" })).toBeInTheDocument();
    expect(screen.queryByLabelText(/out of 5/i)).not.toBeInTheDocument();
    expect(screen.getByText("Verified")).toBeInTheDocument();
    expect(screen.getByText("Pending review")).toBeInTheDocument();
  });

  it("announces current capacity without implying assignment", () => {
    render(<CapacitySignal state="manual_review" detail="A dispatcher must confirm the provider and time." />);
    const status = screen.getByRole("status");
    expect(status).toHaveTextContent("Dispatcher review");
    expect(status).toHaveTextContent("A dispatcher must confirm");
  });

  it("marks exactly the active lifecycle step", () => {
    render(
      <ProjectStatusTimeline
        steps={[
          { id: "request", label: "Request received", status: "complete" },
          { id: "review", label: "Dispatcher review", status: "current" },
          { id: "assignment", label: "Provider assignment", status: "upcoming" },
        ]}
      />,
    );

    const timeline = screen.getByRole("list", { name: "Project progress" });
    expect(within(timeline).getByText("Dispatcher review").closest("li")).toHaveAttribute("aria-current", "step");
    expect(within(timeline).getByText("Provider assignment").closest("li")).not.toHaveAttribute("aria-current");
  });

  it("uses alerts for failures and status semantics for non-error states", () => {
    const { rerender } = render(<MarketplaceStatePanel state="error" title="Unable to load providers" description="Try the request again." />);
    expect(screen.getByRole("alert")).toHaveTextContent("Unable to load providers");

    rerender(<MarketplaceStatePanel state="empty" title="No matching providers" description="Adjust the service area or time window." />);
    const emptyHeading = screen.getByRole("heading", { name: "No matching providers" });
    expect(emptyHeading.closest('[role="status"]')).toHaveTextContent("Adjust the service area or time window");
  });
});

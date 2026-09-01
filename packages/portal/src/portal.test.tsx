import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PortalApiError, portalRequest, toRows } from "./api";
import { formatCell, inferColumns, ResourceView } from "./resource-view";
import { SessionProvider } from "./session";
import type { PortalSection } from "./types";

const BASE = "https://api.example.test/api/v1";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => {
  sessionStorage.clear();
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// Payload shaping
// ---------------------------------------------------------------------------

describe("toRows", () => {
  it("accepts a bare array", () => {
    expect(toRows([{ id: 1 }, { id: 2 }])).toHaveLength(2);
  });

  it("unwraps a paginated envelope", () => {
    expect(toRows({ items: [{ id: 1 }], total: 1 })).toEqual([{ id: 1 }]);
  });

  it("treats a detail object as a single row", () => {
    expect(toRows({ id: 1, status: "ACTIVE" })).toEqual([{ id: 1, status: "ACTIVE" }]);
  });

  it("discards nulls and primitives rather than rendering them", () => {
    expect(toRows([null, 3, { id: 1 }])).toEqual([{ id: 1 }]);
    expect(toRows(null)).toEqual([]);
  });
});

describe("formatCell", () => {
  it("renders an em dash for empty values", () => {
    expect(formatCell(null)).toBe("—");
    expect(formatCell("")).toBe("—");
  });

  it("renders booleans as words", () => {
    expect(formatCell(true)).toBe("Yes");
    expect(formatCell(false)).toBe("No");
  });

  it("never renders [object Object] at an operator", () => {
    expect(String(formatCell({ nested: 1 }))).not.toContain("[object Object]");
  });

  it("makes ISO timestamps readable", () => {
    const rendered = String(formatCell("2026-09-01T10:30:00Z"));
    expect(rendered).not.toBe("2026-09-01T10:30:00Z");
    expect(rendered.length).toBeGreaterThan(0);
  });

  it("leaves ordinary strings alone", () => {
    expect(formatCell("PENDING")).toBe("PENDING");
  });
});

describe("inferColumns", () => {
  it("puts identifying and status columns first", () => {
    const columns = inferColumns([{ zzz: 1, status: "OK", id: "abc", other: 2 }]);
    expect(columns.map((column) => column.key).slice(0, 2)).toEqual(["id", "status"]);
  });

  it("caps the column count so a wide payload stays readable", () => {
    const wide = Object.fromEntries(Array.from({ length: 20 }, (_, i) => [`k${i}`, i]));
    expect(inferColumns([wide])).toHaveLength(6);
  });
});

// ---------------------------------------------------------------------------
// Error translation
// ---------------------------------------------------------------------------

describe("portalRequest", () => {
  it("flattens FastAPI validation detail into readable text", async () => {
    const fetchImpl = vi
      .fn()
      .mockImplementation(async () =>
        jsonResponse(
          { detail: [{ msg: "postal_code is required" }, { msg: "state is invalid" }] },
          422,
        ),
      );
    await expect(
      portalRequest("/thing", { baseUrl: BASE, fetchImpl: fetchImpl as unknown as typeof fetch }),
    ).rejects.toThrow("postal_code is required; state is invalid");
  });

  it("classifies 401 and 403 differently", async () => {
    const unauthorized = new PortalApiError("x", 401);
    const forbidden = new PortalApiError("x", 403);
    expect(unauthorized.isUnauthenticated).toBe(true);
    expect(unauthorized.isForbidden).toBe(false);
    expect(forbidden.isForbidden).toBe(true);
    expect(forbidden.isUnauthenticated).toBe(false);
  });

  it("returns undefined for 204 rather than parsing an empty body", async () => {
    const fetchImpl = vi.fn().mockImplementation(async () => new Response(null, { status: 204 }));
    await expect(
      portalRequest("/thing", {
        method: "DELETE",
        baseUrl: BASE,
        fetchImpl: fetchImpl as unknown as typeof fetch,
      }),
    ).resolves.toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// ResourceView
// ---------------------------------------------------------------------------

const SIGNED_IN = {
  access_token: "token-abc",
  user: { email: "ops@breero.com", full_name: "Ops User", role: "operations" },
};

function renderSection(section: PortalSection) {
  sessionStorage.setItem("breero-portal-session", JSON.stringify(SIGNED_IN));
  return render(
    <SessionProvider allowedRoles={["operations"]}>
      <ResourceView section={section} />
    </SessionProvider>,
  );
}

describe("ResourceView", () => {
  it("states why a capability is blocked instead of showing an empty table", () => {
    render(
      <SessionProvider allowedRoles={["operations"]}>
        <ResourceView
          section={{
            slug: "earnings",
            label: "Earnings",
            description: "d",
            blockedReason: "No provider-scoped endpoint exposes earnings.",
            blockedOn: "The payments release.",
          }}
        />
      </SessionProvider>,
    );
    expect(screen.getByText("Not available yet")).toBeInTheDocument();
    expect(screen.getByText("No provider-scoped endpoint exposes earnings.")).toBeInTheDocument();
    expect(screen.getByText(/The payments release/)).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("renders declared columns rather than raw payload keys", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      jsonResponse([{ id: "job-1", status: "ASSIGNED", internal_debug_field: "noise" }]),
    );
    renderSection({
      slug: "jobs",
      label: "Jobs",
      description: "d",
      source: "/jobs",
      columns: [
        { key: "id", label: "Job" },
        { key: "status", label: "Status" },
      ],
    });
    expect(await screen.findByText("job-1")).toBeInTheDocument();
    expect(screen.getByText("Job")).toBeInTheDocument();
    // A column the section did not declare must not leak into an operator view.
    expect(screen.queryByText("noise")).not.toBeInTheDocument();
  });

  it("distinguishes a permission failure from an outage", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      jsonResponse({ detail: "Forbidden" }, 403),
    );
    renderSection({ slug: "s", label: "S", description: "d", source: "/thing" });
    expect(await screen.findByText(/does not hold the permission/)).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows section-specific empty copy so an empty queue is not a missing feature", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => jsonResponse([]));
    renderSection({
      slug: "dispatch-queue",
      label: "Dispatch queue",
      description: "d",
      source: "/operations/dispatcher/queue",
      emptyTitle: "The queue is clear",
      emptyDescription: "No service requests are waiting.",
    });
    expect(await screen.findByText("The queue is clear")).toBeInTheDocument();
  });

  it("hides an action on rows it does not apply to", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      jsonResponse([
        { id: "1", status: "ACTIVE" },
        { id: "2", status: "SUSPENDED" },
      ]),
    );
    renderSection({
      slug: "vendors",
      label: "Providers",
      description: "d",
      source: "/vendors",
      columns: [{ key: "id", label: "Provider" }],
      actions: [
        {
          label: "Suspend",
          method: "PATCH",
          path: (row) => `/operations/vendors/${String(row.id)}/status`,
          available: (row) => row.status === "ACTIVE",
        },
      ],
    });
    await screen.findByText("1");
    expect(screen.getAllByRole("button", { name: "Suspend" })).toHaveLength(1);
  });

  it("does not send a confirmed action when the operator declines", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(async () => jsonResponse([{ id: "app-1", status: "PENDING" }]));
    vi.spyOn(globalThis, "confirm").mockReturnValue(false);
    renderSection({
      slug: "apps",
      label: "Applications",
      description: "d",
      source: "/admin/provider-applications",
      columns: [{ key: "id", label: "Application" }],
      actions: [
        {
          label: "Approve",
          method: "POST",
          path: (row) => `/admin/provider-applications/${String(row.id)}/approve`,
          confirm: "Approve this application?",
        },
      ],
    });
    await screen.findByText("app-1");
    const callsBefore = fetchMock.mock.calls.length;
    await userEvent.click(screen.getByRole("button", { name: "Approve" }));
    expect(fetchMock.mock.calls).toHaveLength(callsBefore);
  });

  it("sends the action and reloads once confirmed", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(async () => jsonResponse([{ id: "app-1", status: "PENDING" }]));
    vi.spyOn(globalThis, "confirm").mockReturnValue(true);
    renderSection({
      slug: "apps",
      label: "Applications",
      description: "d",
      source: "/admin/provider-applications",
      columns: [{ key: "id", label: "Application" }],
      actions: [
        {
          label: "Approve",
          method: "POST",
          path: (row) => `/admin/provider-applications/${String(row.id)}/approve`,
          confirm: "Approve this application?",
        },
      ],
    });
    await screen.findByText("app-1");
    await userEvent.click(screen.getByRole("button", { name: "Approve" }));
    await waitFor(() => {
      const approve = fetchMock.mock.calls.find(([url]) =>
        String(url).endsWith("/admin/provider-applications/app-1/approve"),
      );
      expect(approve).toBeDefined();
      expect((approve?.[1] as RequestInit).method).toBe("POST");
    });
  });
});

// ---------------------------------------------------------------------------
// Session
// ---------------------------------------------------------------------------

describe("SessionProvider", () => {
  it("clears a corrupt stored session instead of crashing the portal", async () => {
    sessionStorage.setItem("breero-portal-session", "{not json");
    render(
      <SessionProvider allowedRoles={["operations"]}>
        <ResourceView
          section={{ slug: "s", label: "S", description: "d", blockedReason: "blocked" }}
        />
      </SessionProvider>,
    );
    expect(await screen.findByText("Not available yet")).toBeInTheDocument();
    expect(sessionStorage.getItem("breero-portal-session")).toBeNull();
  });

  it("signs the operator out when the API reports an expired token", async () => {
    sessionStorage.setItem("breero-portal-session", JSON.stringify(SIGNED_IN));
    vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      jsonResponse({ detail: "Invalid token" }, 401),
    );
    render(
      <SessionProvider allowedRoles={["operations"]}>
        <ResourceView section={{ slug: "s", label: "S", description: "d", source: "/jobs" }} />
      </SessionProvider>,
    );
    await waitFor(() => expect(sessionStorage.getItem("breero-portal-session")).toBeNull());
  });
});

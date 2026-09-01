"use client";

import { type ChangeEvent, type FormEvent, useState } from "react";

import {
  DataTable,
  formatDate,
  formatLabel,
  PortalConfirmForm,
  PortalError,
  PortalLoading,
  PortalNotice,
  PortalSection,
  StatusBadge,
  type DataColumn,
  usePortalQuery,
  usePortalSession,
} from "@breero/portal";

import type { ListResponse, PostalCode, ServiceZone } from "./admin-types";

export function GeographyPanel({ onChanged }: { onChanged: () => void }) {
  const zones = usePortalQuery<ListResponse<ServiceZone>>(
    "/admin/service-zones?include_inactive=true&limit=200",
  );
  const postal = usePortalQuery<ListResponse<PostalCode>>(
    "/admin/postal-codes?include_inactive=true&limit=500",
  );
  const { request } = usePortalSession();
  const [zoneForm, setZoneForm] = useState({
    name: "",
    country_code: "US",
    timezone_name: "America/New_York",
    boundary: "",
  });
  const [postalForm, setPostalForm] = useState({
    service_zone_id: "",
    country_code: "US",
    postal_code: "",
    city: "",
    state_region: "",
    timezone_name: "America/New_York",
    active: true,
  });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [pendingZone, setPendingZone] = useState<ServiceZone | null>(null);
  const [pendingPostal, setPendingPostal] = useState<PostalCode | null>(null);

  async function createZone(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    try {
      const boundary = JSON.parse(zoneForm.boundary) as Record<string, unknown>;
      await request<ServiceZone>("/admin/service-zones", {
        method: "POST",
        body: JSON.stringify({ ...zoneForm, boundary, active: false }),
      });
      setMessage("Service zone created inactive for review.");
      setZoneForm({ ...zoneForm, name: "", boundary: "" });
      zones.retry();
      onChanged();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to create service zone");
    }
  }

  async function toggleZone(zone: ServiceZone) {
    setError("");
    try {
      await request<ServiceZone>(`/admin/service-zones/${zone.id}`, {
        method: "PATCH",
        body: JSON.stringify({ active: !zone.active }),
      });
      setMessage(`${zone.name} ${zone.active ? "deactivated" : "activated"}.`);
      setPendingZone(null);
      zones.retry();
      onChanged();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to update service zone");
      throw reason;
    }
  }

  async function upsertPostal(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    try {
      await request<PostalCode>("/admin/postal-codes", {
        method: "PUT",
        body: JSON.stringify({
          ...postalForm,
          city: postalForm.city || null,
          state_region: postalForm.state_region || null,
        }),
      });
      setMessage(`${postalForm.postal_code} saved to active service coverage.`);
      setPostalForm({ ...postalForm, postal_code: "", city: "", state_region: "" });
      postal.retry();
      onChanged();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to save postal coverage");
    }
  }

  async function removePostal(item: PostalCode) {
    setError("");
    try {
      await request<void>(`/admin/postal-codes/${item.id}`, { method: "DELETE" });
      setMessage(`${item.postal_code} removed from active coverage.`);
      setPendingPostal(null);
      postal.retry();
      onChanged();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to remove postal coverage");
      throw reason;
    }
  }

  const zoneColumns: DataColumn<ServiceZone>[] = [
    {
      key: "zone",
      label: "Service zone",
      render: (item) => (
        <span>
          <strong>{item.name}</strong>
          <br />
          <small>
            {item.country_code} · {item.timezone_name}
          </small>
        </span>
      ),
    },
    {
      key: "status",
      label: "State",
      compact: true,
      render: (item) => <StatusBadge value={item.active ? "active" : "inactive"} />,
    },
    { key: "updated", label: "Updated", render: (item) => formatDate(item.updated_at) },
    {
      key: "action",
      label: "Action",
      compact: true,
      render: (item) => (
        <button type="button" className="portal-button" onClick={() => setPendingZone(item)}>
          {item.active ? "Review deactivation" : "Review activation"}
        </button>
      ),
    },
  ];
  const postalColumns: DataColumn<PostalCode>[] = [
    {
      key: "postal",
      label: "Postal code",
      render: (item) => (
        <span>
          <strong>{item.postal_code}</strong>
          <br />
          <small>
            {item.city ?? "—"}, {item.state_region ?? "—"}
          </small>
        </span>
      ),
    },
    {
      key: "zone",
      label: "Service zone",
      render: (item) => zones.data?.items.find((zone) => zone.id === item.service_zone_id)?.name ?? item.service_zone_id,
    },
    { key: "timezone", label: "Timezone", render: (item) => item.timezone_name },
    {
      key: "state",
      label: "State",
      compact: true,
      render: (item) => <StatusBadge value={item.active ? "active" : "inactive"} />,
    },
    {
      key: "action",
      label: "Action",
      compact: true,
      render: (item) => (
        <button type="button" className="portal-button" onClick={() => setPendingPostal(item)}>
          Review removal
        </button>
      ),
    },
  ];

  return (
    <div className="portal-stack">
      {message ? (
        <PortalNotice title="Geography updated" tone="success">
          {message}
        </PortalNotice>
      ) : null}
      {error ? (
        <p className="portal-error" role="alert">
          {error}
        </p>
      ) : null}
      <div className="portal-split">
        <PortalSection
          title="Service-zone boundaries"
          subtitle="New boundaries are created inactive and require a separate activation decision."
        >
          <form className="portal-form-grid" onSubmit={(event) => void createZone(event)}>
            <label>
              Zone name
              <input
                required
                maxLength={120}
                value={zoneForm.name}
                onChange={(event: ChangeEvent<HTMLInputElement>) =>
                  setZoneForm({ ...zoneForm, name: event.target.value })
                }
              />
            </label>
            <label>
              Country code
              <input
                required
                minLength={2}
                maxLength={2}
                value={zoneForm.country_code}
                onChange={(event: ChangeEvent<HTMLInputElement>) =>
                  setZoneForm({ ...zoneForm, country_code: event.target.value.toUpperCase() })
                }
              />
            </label>
            <label className="portal-form-span">
              Timezone
              <input
                required
                maxLength={64}
                value={zoneForm.timezone_name}
                onChange={(event: ChangeEvent<HTMLInputElement>) =>
                  setZoneForm({ ...zoneForm, timezone_name: event.target.value })
                }
              />
            </label>
            <label className="portal-form-span">
              GeoJSON Polygon or MultiPolygon
              <textarea
                required
                value={zoneForm.boundary}
                onChange={(event: ChangeEvent<HTMLTextAreaElement>) =>
                  setZoneForm({ ...zoneForm, boundary: event.target.value })
                }
              />
            </label>
            <div className="portal-form-span">
              <button className="portal-button portal-button--primary" type="submit">
                Create inactive zone
              </button>
            </div>
          </form>
          {zones.loading ? <PortalLoading label="Loading service zones" /> : null}
          {zones.error ? <PortalError error={zones.error} onRetry={zones.retry} /> : null}
          {zones.data ? (
            <DataTable
              rows={zones.data.items}
              columns={zoneColumns}
              rowKey={(item) => item.id}
              emptyTitle="No service zones are configured"
            />
          ) : null}
        </PortalSection>
        <PortalSection
          title="Postal fallback coverage"
          subtitle="Postal records must reference a canonical service zone and timezone."
        >
          <form className="portal-form-grid" onSubmit={(event) => void upsertPostal(event)}>
            <label className="portal-form-span">
              Service zone
              <select
                required
                value={postalForm.service_zone_id}
                onChange={(event: ChangeEvent<HTMLSelectElement>) =>
                  setPostalForm({ ...postalForm, service_zone_id: event.target.value })
                }
              >
                <option value="">Choose service zone</option>
                {(zones.data?.items ?? []).map((zone) => (
                  <option key={zone.id} value={zone.id}>
                    {zone.name} · {zone.active ? "Active" : "Inactive"}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Postal code
              <input
                required
                maxLength={16}
                value={postalForm.postal_code}
                onChange={(event: ChangeEvent<HTMLInputElement>) =>
                  setPostalForm({ ...postalForm, postal_code: event.target.value.toUpperCase() })
                }
              />
            </label>
            <label>
              Country
              <input
                required
                minLength={2}
                maxLength={2}
                value={postalForm.country_code}
                onChange={(event: ChangeEvent<HTMLInputElement>) =>
                  setPostalForm({ ...postalForm, country_code: event.target.value.toUpperCase() })
                }
              />
            </label>
            <label>
              City
              <input
                value={postalForm.city}
                onChange={(event: ChangeEvent<HTMLInputElement>) =>
                  setPostalForm({ ...postalForm, city: event.target.value })
                }
              />
            </label>
            <label>
              State / region
              <input
                value={postalForm.state_region}
                onChange={(event: ChangeEvent<HTMLInputElement>) =>
                  setPostalForm({ ...postalForm, state_region: event.target.value })
                }
              />
            </label>
            <label className="portal-form-span">
              Timezone
              <input
                required
                maxLength={64}
                value={postalForm.timezone_name}
                onChange={(event: ChangeEvent<HTMLInputElement>) =>
                  setPostalForm({ ...postalForm, timezone_name: event.target.value })
                }
              />
            </label>
            <div className="portal-form-span">
              <button className="portal-button portal-button--primary" type="submit">
                Save postal coverage
              </button>
            </div>
          </form>
          {postal.loading ? <PortalLoading label="Loading postal coverage" /> : null}
          {postal.error ? <PortalError error={postal.error} onRetry={postal.retry} /> : null}
          {postal.data ? (
            <DataTable
              rows={postal.data.items}
              columns={postalColumns}
              rowKey={(item) => item.id}
              emptyTitle="No postal coverage is configured"
            />
          ) : null}
        </PortalSection>
      </div>
      {pendingZone ? (
        <PortalSection
          title={`${pendingZone.active ? "Deactivate" : "Activate"} service zone`}
          subtitle="Activation changes marketplace eligibility for every matching address inside this boundary."
        >
          <PortalConfirmForm
            title={`${pendingZone.active ? "Deactivate" : "Activate"} ${pendingZone.name}`}
            description={
              pendingZone.active
                ? "Deactivation removes this boundary from active service-area decisions. Existing records remain retained."
                : "Activation makes this reviewed boundary eligible for address and service-zone decisions."
            }
            confirmLabel={pendingZone.active ? "Deactivate zone" : "Activate zone"}
            onConfirm={() => toggleZone(pendingZone)}
          />
        </PortalSection>
      ) : null}
      {pendingPostal ? (
        <PortalSection
          title="Remove postal coverage"
          subtitle="This is a soft removal from active fallback coverage; the record remains retained for evidence."
        >
          <PortalConfirmForm
            title={`Remove ${pendingPostal.postal_code}`}
            description="Confirm that this postal code should no longer resolve to its current BREERO service zone."
            confirmLabel="Remove postal coverage"
            onConfirm={() => removePostal(pendingPostal)}
          />
        </PortalSection>
      ) : null}
    </div>
  );
}

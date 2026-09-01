"use client";

import { useCallback } from "react";
import { Card, EmptyState, ErrorState, HomeIcon, LoadingState } from "@breero/ui";
import { AccountPageHeader } from "@/components/account/page-header";
import { customerApi } from "@/lib/customer/api";
import { useApiResource } from "@/lib/customer/use-api-resource";

export default function AddressesPage() {
  const load = useCallback((signal: AbortSignal) => customerApi.customer.addresses(signal), []);
  const { value: addresses, error, retry } = useApiResource(load);
  return (
    <>
      <AccountPageHeader
        eyebrow="Your places"
        title="Saved addresses"
        description="Choose where you need help more quickly when you book."
      />
      {error ? (
        <ErrorState
          title="Addresses aren’t available"
          description={error.message}
          onRetry={retry}
        />
      ) : !addresses ? (
        <LoadingState label="Loading saved addresses" />
      ) : addresses.length ? (
        <Card>
          <div className="address-list">
            {addresses.map((address) => (
              <article className="address-card" key={address.id}>
                <span>
                  <HomeIcon />
                </span>
                <div>
                  <strong>Saved address</strong>
                  <small>
                    {address.line1}, {address.postal_code} {address.city}, {address.country_code}
                  </small>
                </div>
              </article>
            ))}
          </div>
        </Card>
      ) : (
        <EmptyState
          title="No saved addresses"
          description="Validated addresses can be saved from your booking journey."
        />
      )}
    </>
  );
}

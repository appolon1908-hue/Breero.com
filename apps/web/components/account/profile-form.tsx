"use client";

import { useCallback, useState } from "react";
import { Button, ErrorState, FormField, Input, LoadingState } from "@breero/ui";
import { customerApi } from "@/lib/customer/api";
import { useApiResource } from "@/lib/customer/use-api-resource";

export function ProfileForm() {
  const load = useCallback((signal: AbortSignal) => customerApi.customer.profile(signal), []);
  const { value: profile, error, retry } = useApiResource(load);
  const [state, setState] = useState<"idle" | "loading" | "success" | "error">("idle");
  if (error)
    return (
      <ErrorState
        title="Your profile isn’t available"
        description={error.message}
        onRetry={retry}
      />
    );
  if (!profile) return <LoadingState label="Loading your profile" />;
  async function submit(data: FormData) {
    setState("loading");
    try {
      await customerApi.customer.updateProfile({
        full_name: String(data.get("full_name")),
        phone: String(data.get("phone")),
      });
      setState("success");
    } catch {
      setState("error");
    }
  }
  return (
    <form className="profile-form" action={submit}>
      <FormField label="Full name" htmlFor="full_name" required>
        <Input
          id="full_name"
          name="full_name"
          defaultValue={profile.full_name}
          required
          autoComplete="name"
        />
      </FormField>
      <FormField
        label="Phone number"
        htmlFor="phone"
        hint="Used only for important booking updates."
      >
        <Input id="phone" name="phone" type="tel" defaultValue={profile.phone} autoComplete="tel" />
      </FormField>
      <FormField
        label="Email"
        htmlFor="email"
        hint="Email changes require verification before taking effect."
      >
        <Input id="email" type="email" defaultValue={profile.email} disabled />
      </FormField>
      <p>
        Manage email and SMS choices on the{" "}
        <a href="/communications-preferences">communications preferences page</a>.
      </p>
      {state === "success" && (
        <p className="auth-message" role="status">
          Your profile has been updated.
        </p>
      )}
      {state === "error" && (
        <p className="auth-message auth-error" role="alert">
          We couldn’t save your changes. Try again.
        </p>
      )}
      <Button type="submit" loading={state === "loading"}>
        Save changes
      </Button>
    </form>
  );
}

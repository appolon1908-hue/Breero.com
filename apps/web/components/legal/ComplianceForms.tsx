"use client";
import { FormEvent, useState } from "react";
type SubmissionState = { status: "idle" | "sending" | "success" | "error"; message: string };
const initialState: SubmissionState = { status: "idle", message: "" };
async function submitForm(
  event: FormEvent<HTMLFormElement>,
  endpoint: string,
  setState: (state: SubmissionState) => void,
) {
  event.preventDefault();
  const form = event.currentTarget;
  setState({ status: "sending", message: "" });
  try {
    const response = await fetch(endpoint, { method: "POST", body: new FormData(form) });
    const result = (await response.json().catch(() => ({}))) as {
      detail?: string | Array<{ msg?: string }>;
      request_id?: string;
    };
    if (!response.ok) {
      const detail = Array.isArray(result.detail)
        ? result.detail
            .map((item) => item.msg)
            .filter(Boolean)
            .join(" ")
        : result.detail;
      throw new Error(detail || "We could not save your request.");
    }
    form.reset();
    setState({
      status: "success",
      message: result.request_id
        ? `Request received. Reference: ${result.request_id}`
        : "Your preferences have been recorded.",
    });
  } catch (error) {
    setState({
      status: "error",
      message: error instanceof Error ? error.message : "The service is temporarily unavailable.",
    });
  }
}
export function CommunicationPreferencesForm() {
  const [state, setState] = useState(initialState);
  return (
    <form
      className="compliance-form"
      onSubmit={(event) => void submitForm(event, "/api/communications/preferences", setState)}
      aria-busy={state.status === "sending"}
    >
      <label>
        Email or phone <input name="destination" required minLength={5} />
      </label>
      <fieldset>
        <legend>Preferences</legend>
        <label>
          <input type="checkbox" name="transactionalEmail" /> Transactional appointment email
        </label>
        <label>
          <input type="checkbox" name="transactionalSms" /> Transactional appointment SMS
        </label>
        <label>
          <input type="checkbox" name="marketingEmail" /> Marketing email (not currently active)
        </label>
        <label>
          <input type="checkbox" name="marketingSms" /> Marketing SMS (not currently active)
        </label>
      </fieldset>
      <button type="submit" disabled={state.status === "sending"}>
        {state.status === "sending" ? "Saving…" : "Save preferences"}
      </button>
      <p role={state.status === "error" ? "alert" : "status"}>{state.message}</p>
    </form>
  );
}
export function PrivacyRequestForm() {
  const [state, setState] = useState(initialState);
  return (
    <form
      className="compliance-form"
      onSubmit={(event) => void submitForm(event, "/api/privacy-requests", setState)}
      aria-busy={state.status === "sending"}
    >
      <label>
        Request type{" "}
        <select name="requestType" required defaultValue="">
          <option value="" disabled>
            Select one
          </option>
          <option value="access">Access</option>
          <option value="correction">Correction</option>
          <option value="deletion">Deletion</option>
          <option value="portability">Portability</option>
          <option value="opt_out_sale_sharing">Opt out of sale or sharing</option>
          <option value="opt_out_targeted_ads">Opt out of targeted advertising</option>
          <option value="appeal">Appeal</option>
        </select>
      </label>
      <label>
        Email <input name="email" type="email" autoComplete="email" required />
      </label>
      <button type="submit" disabled={state.status === "sending"}>
        {state.status === "sending" ? "Submitting…" : "Submit privacy request"}
      </button>
      <p role={state.status === "error" ? "alert" : "status"}>{state.message}</p>
    </form>
  );
}

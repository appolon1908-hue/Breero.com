import { readPublicApiConfig } from "@breero/api-client";

export class PortalApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "PortalApiError";
  }

  /** A signed-out or expired session, as opposed to a genuine permission failure. */
  get isUnauthenticated(): boolean {
    return this.status === 401;
  }

  get isForbidden(): boolean {
    return this.status === 403;
  }
}

/**
 * Resolve the API origin through the shared, already-tested config reader rather than
 * a local regex. It permits localhost during development and enforces the real origin
 * in production, which a bare `https://` check does not.
 */
export function portalApiBase(env: Record<string, string | undefined> = process.env): string {
  return readPublicApiConfig(env).apiBaseUrl.replace(/\/$/, "");
}

export interface PortalRequestOptions {
  method?: string;
  body?: unknown;
  token?: string;
  signal?: AbortSignal;
  baseUrl?: string;
  fetchImpl?: typeof globalThis.fetch;
}

export async function portalRequest<T>(
  path: string,
  options: PortalRequestOptions = {},
): Promise<T> {
  const { method = "GET", body, token, signal, baseUrl, fetchImpl } = options;
  const headers = new Headers({ Accept: "application/json" });
  if (body !== undefined) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const doFetch = fetchImpl ?? globalThis.fetch.bind(globalThis);
  const response = await doFetch(`${baseUrl ?? portalApiBase()}${path}`, {
    method,
    headers,
    signal,
    cache: "no-store",
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as {
      message?: string;
      detail?: unknown;
    };
    // FastAPI puts validation errors in `detail` as an array, and this portal is where
    // an operator sees them. Rendering "[object Object]" at that moment is not an
    // option, so collapse structured detail into something readable.
    const detail =
      typeof payload.detail === "string"
        ? payload.detail
        : Array.isArray(payload.detail)
          ? payload.detail
              .map((item) =>
                item && typeof item === "object" && "msg" in item
                  ? String((item as { msg: unknown }).msg)
                  : JSON.stringify(item),
              )
              .join("; ")
          : undefined;
    throw new PortalApiError(
      payload.message ?? detail ?? `Request failed (${response.status})`,
      response.status,
    );
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

/**
 * Normalise the shapes the API returns into rows.
 *
 * Collections come back either bare or wrapped in `items`, and a detail endpoint
 * returns a single object. A section should not have to know which.
 */
export function toRows(value: unknown): Record<string, unknown>[] {
  const isRow = (item: unknown): item is Record<string, unknown> =>
    Boolean(item) && typeof item === "object" && !Array.isArray(item);

  if (Array.isArray(value)) return value.filter(isRow);
  if (isRow(value) && Array.isArray((value as { items?: unknown }).items)) {
    return ((value as { items: unknown[] }).items ?? []).filter(isRow);
  }
  return isRow(value) ? [value] : [];
}

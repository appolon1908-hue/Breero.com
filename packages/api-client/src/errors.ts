export type ApiErrorKind =
  | "validation"
  | "authentication"
  | "forbidden"
  | "not_found"
  | "conflict"
  | "unavailable"
  | "rate_limit"
  | "server"
  | "network"
  | "timeout"
  | "cancelled"
  | "unknown";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly kind: ApiErrorKind,
    readonly status?: number,
    readonly code?: string,
    readonly requestId?: string,
    readonly details?: unknown,
    readonly retryAfterSeconds?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const kindForStatus = (status: number): ApiErrorKind => {
  if (status === 401) return "authentication";
  if (status === 403) return "forbidden";
  if (status === 404) return "not_found";
  if (status === 409) return "conflict";
  if (status === 422 || status === 400) return "validation";
  if (status === 429) return "rate_limit";
  if (status === 502 || status === 503 || status === 504) return "unavailable";
  if (status >= 500) return "server";
  return "unknown";
};

export async function apiErrorFromResponse(response: Response): Promise<ApiError> {
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    body = undefined;
  }
  const record = body && typeof body === "object" ? (body as Record<string, unknown>) : {};
  const nested =
    record.error && typeof record.error === "object"
      ? (record.error as Record<string, unknown>)
      : {};
  const detail = record.detail;
  const details = Array.isArray(detail)
    ? detail.map((item) => {
        const issue = item && typeof item === "object" ? (item as Record<string, unknown>) : {};
        return {
          field: Array.isArray(issue.loc) ? issue.loc.join(".") : undefined,
          message: typeof issue.msg === "string" ? issue.msg : "Invalid value",
          code: typeof issue.type === "string" ? issue.type : undefined,
        };
      })
    : detail;
  const message =
    typeof nested.message === "string"
      ? nested.message
      : typeof detail === "string"
        ? detail
        : `Request failed (${response.status})`;
  const retryAfter = Number(response.headers.get("retry-after"));
  return new ApiError(
    message,
    kindForStatus(response.status),
    response.status,
    typeof nested.code === "string" ? nested.code : undefined,
    response.headers.get("x-request-id") ?? undefined,
    details,
    Number.isFinite(retryAfter) ? retryAfter : undefined,
  );
}

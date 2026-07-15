// Typed fetch wrapper. Sends the session cookie and the X-Requested-With header
// (required by the backend CSRF check on mutating requests, added in Phase 1).

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Normalize FastAPI `detail` (string or 422 validation array) for UI display. */
export function formatApiDetail(detail: unknown, fallback: string): string {
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        if (item && typeof item === "object") {
          const entry = item as { loc?: unknown[]; msg?: unknown };
          const loc = Array.isArray(entry.loc)
            ? entry.loc
                .filter((part) => part !== "body" && part !== "query" && part !== "path")
                .join(".")
            : "";
          const msg = typeof entry.msg === "string" ? entry.msg : "";
          if (loc && msg) {
            return `${loc}: ${msg}`;
          }
          return msg || loc;
        }
        return "";
      })
      .filter(Boolean);
    return parts.length > 0 ? parts.join("; ") : fallback;
  }
  if (detail != null && typeof detail === "object") {
    try {
      return JSON.stringify(detail);
    } catch {
      // fall through
    }
  }
  return fallback;
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  options?: { parseJson?: boolean },
): Promise<T> {
  const parseJson = options?.parseJson ?? true;
  const resp = await fetch(`/api${path}`, {
    method,
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      "X-Requested-With": "XMLHttpRequest",
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!resp.ok) {
    let detail: unknown = resp.statusText;
    try {
      const data = (await resp.json()) as { detail?: unknown };
      detail = data.detail ?? detail;
    } catch {
      // non-JSON error body; keep statusText
    }
    throw new ApiError(resp.status, formatApiDetail(detail, resp.statusText));
  }

  if (resp.status === 204) return undefined as T;
  if (!parseJson) {
    return (await resp.text()) as T;
  }
  return resp.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  getText: (path: string) => request<string>("GET", path, undefined, { parseJson: false }),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
  put: <T>(path: string, body?: unknown) => request<T>("PUT", path, body),
  del: <T>(path: string) => request<T>("DELETE", path),
};

// Single typed API client. Base URL is configurable via VITE_API_BASE_URL;
// when blank we rely on the Vite dev proxy (see vite.config.ts).
const BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await res.text();
  const body = text ? JSON.parse(text) : {};
  if (!res.ok) {
    const err: ApiError = body.error ?? {
      code: "http_error",
      message: res.statusText,
    };
    throw err;
  }
  return body as T;
}

export const api = {
  get: <T>(p: string) => request<T>(p),
  post: <T>(p: string, data?: unknown) =>
    request<T>(p, { method: "POST", body: JSON.stringify(data ?? {}) }),
  put: <T>(p: string, data?: unknown) =>
    request<T>(p, { method: "PUT", body: JSON.stringify(data ?? {}) }),
  postForm: async <T>(p: string, form: FormData): Promise<T> => {
    const res = await fetch(BASE + p, { method: "POST", body: form });
    const body = await res.json();
    if (!res.ok) throw body.error ?? { code: "http_error", message: "failed" };
    return body as T;
  },
};

export interface ProviderResult {
  ok: boolean;
  provider: string;
  detail?: string;
  [k: string]: unknown;
}

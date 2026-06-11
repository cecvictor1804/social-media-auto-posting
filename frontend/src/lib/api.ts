// Typed fetch client. Sends the session cookie with every call; a 401 means the
// session expired or is missing -> bounce to the login page (unless told not to,
// which the auth probe uses so the Login screen itself doesn't loop).

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

interface Options extends Omit<RequestInit, "body"> {
  body?: unknown;
  noRedirect?: boolean;
}

async function request<T>(path: string, opts: Options = {}): Promise<T> {
  const { body, noRedirect, headers, ...rest } = opts;
  const res = await fetch(path, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...headers },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    ...rest,
  });

  if (res.status === 401) {
    if (!noRedirect && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
    throw new ApiError(401, "Not authenticated");
  }

  if (!res.ok) {
    let message = res.statusText;
    try {
      const data = await res.json();
      if (data?.detail) message = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch {
      /* ignore non-JSON error bodies */
    }
    throw new ApiError(res.status, message);
  }

  if (res.status === 204) return null as T;
  const ct = res.headers.get("content-type") || "";
  return (ct.includes("application/json") ? await res.json() : await res.text()) as T;
}

async function uploadFile<T>(path: string, file: File): Promise<T> {
  const form = new FormData();
  form.append("file", file);
  // No JSON Content-Type — let the browser set the multipart boundary.
  const res = await fetch(path, { method: "POST", credentials: "include", body: form });
  if (res.status === 401) {
    if (!window.location.pathname.startsWith("/login")) window.location.href = "/login";
    throw new ApiError(401, "Not authenticated");
  }
  if (!res.ok) {
    let message = res.statusText;
    try {
      const data = await res.json();
      if (data?.detail) message = String(data.detail);
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, message);
  }
  return (await res.json()) as T;
}

export const api = {
  get: <T>(path: string, opts?: Options) => request<T>(path, { ...opts, method: "GET" }),
  post: <T>(path: string, body?: unknown, opts?: Options) =>
    request<T>(path, { ...opts, method: "POST", body }),
  patch: <T>(path: string, body?: unknown, opts?: Options) =>
    request<T>(path, { ...opts, method: "PATCH", body }),
  del: <T>(path: string, opts?: Options) => request<T>(path, { ...opts, method: "DELETE" }),
  upload: uploadFile,
};

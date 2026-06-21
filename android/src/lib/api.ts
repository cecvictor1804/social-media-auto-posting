// Typed fetch client for the mobile app.
// Uses Bearer token (stored in expo-secure-store) instead of the web's session cookie.

import { clearToken, getToken } from "./auth";
import { ApiError } from "./errors";

const API_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://10.0.2.2:8000";

interface Options extends Omit<RequestInit, "body"> {
  body?: unknown;
}

async function request<T>(path: string, opts: Options = {}): Promise<T> {
  const { body, headers, ...rest } = opts;
  const token = await getToken();

  const reqHeaders: Record<string, string> = {
    ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(headers as Record<string, string>),
  };

  const res = await fetch(`${API_URL}${path}`, {
    headers: reqHeaders,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    ...rest,
  });

  if (res.status === 401) {
    await clearToken();
    throw new ApiError(401, "Not authenticated");
  }

  if (!res.ok) {
    let message = res.statusText;
    try {
      const data = await res.json();
      if (data?.detail)
        message = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch {
      /* ignore non-JSON error bodies */
    }
    throw new ApiError(res.status, message);
  }

  if (res.status === 204) return null as T;
  const ct = res.headers.get("content-type") ?? "";
  return (ct.includes("application/json") ? await res.json() : await res.text()) as T;
}

export interface UploadAsset {
  uri: string;
  name: string;
  type: string;
}

async function uploadFile<T>(path: string, asset: UploadAsset): Promise<T> {
  const token = await getToken();
  const form = new FormData();
  // React Native FormData accepts {uri, name, type} objects
  form.append("file", { uri: asset.uri, name: asset.name, type: asset.type } as unknown as Blob);

  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });

  if (res.status === 401) {
    await clearToken();
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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type TokenPair = { access_token: string; refresh_token: string };

function authHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string, totp_code?: string) =>
    apiFetch<TokenPair>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password, totp_code }),
    }),
  me: () =>
    apiFetch<{ email: string; totp_enabled: boolean }>("/api/v1/auth/me"),
  devices: () => apiFetch<Device[]>("/api/v1/devices"),
  device: (id: string) => apiFetch<Device>(`/api/v1/devices/${id}`),
  approveDevice: (id: string) =>
    apiFetch<Device>(`/api/v1/devices/${id}/approve`, { method: "POST" }),
  locations: (id: string) =>
    apiFetch<LocationPoint[]>(`/api/v1/devices/${id}/locations`),
  createEnrollmentCode: () =>
    apiFetch<{ code: string; expires_at: string }>("/api/v1/enrollment/codes", {
      method: "POST",
      body: JSON.stringify({}),
    }),
  commands: (deviceId?: string) =>
    apiFetch<Command[]>(
      `/api/v1/commands${deviceId ? `?device_id=${deviceId}` : ""}`,
    ),
  createCommand: (device_id: string, type: string, idempotencyKey?: string) =>
    apiFetch<Command>("/api/v1/commands", {
      method: "POST",
      headers: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {},
      body: JSON.stringify({ device_id, type, payload: {} }),
    }),
  audit: () => apiFetch<AuditEntry[]>("/api/v1/audit"),
  settings: () => apiFetch<{ location_retention_days: number }>("/api/v1/settings"),
  updateSettings: (location_retention_days: number) =>
    apiFetch<{ location_retention_days: number }>("/api/v1/settings", {
      method: "PUT",
      body: JSON.stringify({ location_retention_days }),
    }),
  updateSmsSenders: (deviceId: string, phone_numbers: string[]) =>
    apiFetch<{ phone_numbers: string[] }>(
      `/api/v1/devices/${deviceId}/sms-senders`,
      {
        method: "PUT",
        body: JSON.stringify({ phone_numbers }),
      },
    ),
};

export type Device = {
  id: string;
  name: string;
  model: string | null;
  manufacturer: string | null;
  android_version: string | null;
  mode: string;
  status: string;
  capabilities: Record<string, string>;
  last_seen_at: string | null;
  battery_level: number | null;
  online: boolean;
  enrolled_at: string;
  approved_at: string | null;
};

export type LocationPoint = {
  latitude: number;
  longitude: number;
  accuracy: number | null;
  recorded_at: string;
};

export type Command = {
  id: string;
  device_id: string;
  type: string;
  status: string;
  result: Record<string, unknown> | null;
  created_at: string;
  completed_at: string | null;
};

export type AuditEntry = {
  id: string;
  action: string;
  details: Record<string, unknown>;
  created_at: string;
};

export function capabilityLabel(state: string): string {
  const map: Record<string, string> = {
    supported_and_ready: "پشتیبانی و آماده",
    requires_permission: "نیاز به مجوز",
    requires_device_owner: "نیاز به Device Owner",
    requires_user_confirmation: "نیاز به تأیید کاربر",
    unsupported: "پشتیبانی نمی‌شود",
  };
  return map[state] || state;
}

export function commandStatusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: "در انتظار",
    delivered: "تحویل به دستگاه",
    completed: "تکمیل شده",
    failed: "ناموفق",
    rejected: "رد شده",
    expired: "منقضی",
  };
  return map[status] || status;
}

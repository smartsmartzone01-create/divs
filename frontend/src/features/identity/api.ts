export type AuthAccount = {
  id: string;
  email: string | null;
  phone_number: string | null;
  country_code: string;
  email_verified: boolean;
  phone_verified: boolean;
  date_joined: string;
};

export type AuthSession = {
  id: string;
  device_label: string;
  ip_address: string | null;
  created_at: string;
  last_seen_at: string;
  expires_at: string;
  revoked_at: string | null;
  current: boolean;
};

export class IdentityApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly payload?: unknown,
  ) {
    super(message);
    this.name = "IdentityApiError";
  }
}

export async function identityRequest<T>(
  path: string,
  options: { method?: "GET" | "POST" | "PATCH" | "DELETE"; body?: unknown } = {},
): Promise<T> {
  const response = await fetch(`/api/auth/${path.replace(/^\/+|\/+$/g, "")}/`, {
    method: options.method ?? "GET",
    headers: {
      Accept: "application/json",
      ...(options.body === undefined ? {} : { "Content-Type": "application/json" }),
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    credentials: "same-origin",
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    let payload: unknown = text;
    try {
      payload = text ? JSON.parse(text) : undefined;
    } catch {
      // Preserve a non-JSON error body for diagnostics.
    }
    const detail =
      typeof payload === "object" && payload !== null && "detail" in payload
        ? String((payload as { detail: unknown }).detail)
        : `Authentication request failed (${response.status}).`;
    throw new IdentityApiError(detail, response.status, payload);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function signIn(identifier: string, password: string) {
  return identityRequest<{ session_id: string }>("token", {
    method: "POST",
    body: { identifier, password },
  });
}

export async function registerAccount(input: {
  email?: string;
  phone_number?: string;
  country_code?: string;
  password: string;
}) {
  return identityRequest<AuthAccount>("register", { method: "POST", body: input });
}

export async function requestVerification(input: { channel: "email" | "phone"; email?: string; phone_number?: string }) {
  return identityRequest<{ detail: string }>("verification/request", {
    method: "POST",
    body: input,
  });
}

export async function confirmVerification(input: { channel: "email" | "phone"; email?: string; phone_number?: string; code: string }) {
  return identityRequest<{ verified: boolean }>("verification/confirm", {
    method: "POST",
    body: input,
  });
}

export async function requestPasswordReset(input: { email?: string; phone_number?: string }) {
  return identityRequest<{ detail: string }>("password-reset/request", {
    method: "POST",
    body: input,
  });
}

export async function confirmPasswordReset(input: {
  email?: string;
  phone_number?: string;
  code: string;
  new_password: string;
}) {
  return identityRequest<{ detail: string }>("password-reset/confirm", {
    method: "POST",
    body: input,
  });
}

export async function getCurrentAccount() {
  return identityRequest<AuthAccount>("me");
}

export async function getSessions() {
  return identityRequest<AuthSession[]>("sessions");
}

export async function logout() {
  return identityRequest<void>("logout", { method: "POST", body: {} });
}

export async function revokeSession(sessionId: string) {
  return identityRequest<void>(`sessions/${sessionId}`, { method: "DELETE" });
}

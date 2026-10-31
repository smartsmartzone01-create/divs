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

type OperationsAccess = {
  role: "admin" | "operator";
  capabilities: string[];
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
  const response = await fetch(`/api/auth/${path.replace(/^\\/+|\\/+$/g, "")}/`, {
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
    let detail = `Authentication request failed (${response.status}).`;
    if (typeof payload === "string" && payload) {
      detail = payload;
    } else if (typeof payload === "object" && payload !== null) {
      const record = payload as Record<string, unknown>;
      if (typeof record.detail === "string") {
        detail = record.detail;
      } else if (Array.isArray(record.non_field_errors)) {
        detail = record.non_field_errors.map(String).join(" ");
      } else {
        const firstFieldError = Object.entries(record).find(([, value]) => value !== undefined);
        if (firstFieldError) {
          const [field, value] = firstFieldError;
          const message = Array.isArray(value) ? value.map(String).join(" ") : String(value);
          detail = `${field.replace(/_/g, " ")}: ${message}`;
        }
      }
    }
    throw new IdentityApiError(detail, response.status, payload);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

async function getOperationsAccess(): Promise<OperationsAccess | null> {
  try {
    const response = await fetch("/api/backend/operations/me/", {
      credentials: "same-origin",
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) return null;
    return (await response.json()) as OperationsAccess;
  } catch {
    return null;
  }
}

/**
 * Resolve the landing page from backend-authorized operations access.
 * A client-side role hint is never used to grant access; the workspace
 * independently checks the same protected backend endpoint.
 */
export async function getPostLoginPath(): Promise<string> {
  const access = await getOperationsAccess();
  return access && (access.role === "admin" || access.role === "operator")
    ? "/workspace/admin"
    : "/account";
}

export async function hasOperationsWorkspaceAccess(): Promise<boolean> {
  return (await getOperationsAccess()) !== null;
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

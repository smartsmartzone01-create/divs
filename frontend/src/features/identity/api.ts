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

export type AccountMenuDetails = {
  displayName: string;
  initials: string;
  roleLabel: string;
  workspaceHref: string;
  workspaceLabel: string;
};

async function getProfile<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(path, {
      credentials: "same-origin",
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

/** Resolve the account menu from the signed-in user's own protected profile endpoints. */
export async function getAccountMenuDetails(): Promise<AccountMenuDetails> {
  const account = await getCurrentAccount();
  let displayName = "";
  let roleLabel = "DIVS account";
  let workspaceHref = "/account";
  let workspaceLabel = "My account";

  const operationsAccess = await getOperationsAccess();
  if (operationsAccess) {
    const profile = await getProfile<{ full_name?: string }>("/api/backend/profiles/operations/");
    displayName = profile?.full_name?.trim() ?? "";
    roleLabel = operationsAccess.role === "admin" ? "Administrator" : "Operations operator";
    workspaceHref = "/workspace/admin";
    workspaceLabel = "Open admin workspace";
  } else {
    const driver = await getProfile<{ registration?: { first_name?: string; middle_name?: string; last_name?: string } }>("/api/backend/profiles/driver/");
    if (driver?.registration) {
      const person = driver.registration;
      displayName = [person.first_name, person.middle_name, person.last_name].filter(Boolean).join(" ");
      roleLabel = "Driver";
      workspaceLabel = "My account";
    } else {
      const client = await getProfile<{ registration?: { name?: string } }>("/api/backend/profiles/client/");
      if (client?.registration) {
        displayName = client.registration.name?.trim() ?? "";
        roleLabel = "Client";
        workspaceLabel = "My account";
      }
    }
  }

  if (!displayName) displayName = account.email?.split("@")[0]?.replace(/[._-]+/g, " ").trim() || account.phone_number || "DIVS account";
  const parts = displayName.split(/\s+/).filter(Boolean);
  const initials = parts.length > 1
    ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
    : (parts[0]?.slice(0, 2) || "U").toUpperCase();

  return { displayName, initials, roleLabel, workspaceHref, workspaceLabel };
}


export type DriverRegistration = {
  id: string;
  first_name: string;
  middle_name: string;
  last_name: string;
  nationality: string;
  region: string;
  district: string;
  residential_area: string;
  current_residential_address: string;
  driving_experience: "none" | "under_1_year" | "1_to_3_years" | "4_to_7_years" | "8_plus_years";
  contact_email: string | null;
  contact_phone_number: string | null;
  created_at: string;
  updated_at: string;
};

export async function getDriverRegistration(): Promise<DriverRegistration | null> {
  const response = await fetch("/api/backend/registrations/driver/", {
    credentials: "same-origin",
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (response.status === 404) return null;
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail || `Could not load driver registration (${response.status}).`);
  }
  return response.json() as Promise<DriverRegistration>;
}

export async function submitDriverRegistration(input: Omit<DriverRegistration, "id" | "contact_email" | "contact_phone_number" | "created_at" | "updated_at">): Promise<DriverRegistration> {
  const response = await fetch("/api/backend/registrations/driver/", {
    method: "POST",
    credentials: "same-origin",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const first = payload && typeof payload === "object"
      ? Object.entries(payload).find(([, value]) => value !== undefined)
      : null;
    const message = typeof payload?.detail === "string"
      ? payload.detail
      : first
        ? `${first[0].replace(/_/g, " ")}: ${Array.isArray(first[1]) ? first[1].join(" ") : String(first[1])}`
        : `Driver registration failed (${response.status}).`;
    throw new Error(message);
  }
  return payload as DriverRegistration;
}

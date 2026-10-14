import { NextRequest, NextResponse } from "next/server";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

const ACCESS_COOKIE = "divs_access";
const REFRESH_COOKIE = "divs_refresh";
const ACCESS_MAX_AGE = 15 * 60;
const REFRESH_MAX_AGE = 7 * 24 * 60 * 60;

function apiBaseUrl(): string {
  const value =
    process.env.DIVS_API_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    "http://127.0.0.1:8000/api/v1";
  return value.replace(/\/+$/, "");
}

function applyAuthCookies(response: NextResponse, tokens: { access: string; refresh: string }) {
  const common = {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/api",
  };
  response.cookies.set(ACCESS_COOKIE, tokens.access, { ...common, maxAge: ACCESS_MAX_AGE });
  response.cookies.set(REFRESH_COOKIE, tokens.refresh, { ...common, maxAge: REFRESH_MAX_AGE });
}

function clearAuthCookies(response: NextResponse) {
  const common = {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/api",
    maxAge: 0,
  };
  response.cookies.set(ACCESS_COOKIE, "", common);
  response.cookies.set(REFRESH_COOKIE, "", common);
}

async function upstreamRequest(
  request: NextRequest,
  routePath: string,
  accessToken?: string,
  body?: string,
) {
  const url = `${apiBaseUrl()}/auth/${routePath}/${request.nextUrl.search}`;
  const headers = new Headers({ Accept: "application/json" });
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("Content-Type", contentType);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);

  return fetch(url, {
    method: request.method,
    headers,
    body: request.method === "GET" || request.method === "HEAD" ? undefined : body,
    cache: "no-store",
    redirect: "manual",
  });
}

async function makeResponse(upstream: Response): Promise<NextResponse> {
  const text = await upstream.text();
  const headers = new Headers();
  const contentType = upstream.headers.get("content-type");
  if (contentType) headers.set("Content-Type", contentType);
  return new NextResponse(text || null, { status: upstream.status, headers });
}

async function handler(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  if (!path.length || path.some((part) => !/^[A-Za-z0-9_-]+$/.test(part))) {
    return NextResponse.json({ detail: "Invalid authentication route." }, { status: 400 });
  }

  const routePath = path.join("/");
  const body =
    request.method === "GET" || request.method === "HEAD" ? undefined : await request.text();
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;
  let accessToken = request.cookies.get(ACCESS_COOKIE)?.value;
  const tokenlessRoutes = new Set([
    "register",
    "token",
    "verification/request",
    "verification/confirm",
    "password-reset/request",
    "password-reset/confirm",
    "providers/google",
    "providers/phone",
  ]);
  let upstream: Response;

  if (routePath === "token/refresh" && request.method === "POST") {
    if (!refreshToken) {
      const response = NextResponse.json({ detail: "No active refresh session." }, { status: 401 });
      clearAuthCookies(response);
      return response;
    }
    upstream = await fetch(`${apiBaseUrl()}/auth/token/refresh/`, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: refreshToken }),
      cache: "no-store",
    });
  } else {
    upstream = await upstreamRequest(request, routePath, tokenlessRoutes.has(routePath) ? undefined : accessToken, body);
  }

  let rotatedTokens: { access: string; refresh: string } | undefined;

  // Retry a protected request once when its access token has expired.
  if (
    upstream.status === 401 &&
    refreshToken &&
    !tokenlessRoutes.has(routePath) &&
    routePath !== "token" &&
    routePath !== "token/refresh"
  ) {
    const refreshResponse = await fetch(`${apiBaseUrl()}/auth/token/refresh/`, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: refreshToken }),
      cache: "no-store",
    });
    const refreshed = (await refreshResponse.json().catch(() => null)) as
      | { access?: string; refresh?: string }
      | null;

    if (refreshResponse.ok && refreshed?.access && refreshed.refresh) {
      rotatedTokens = { access: refreshed.access, refresh: refreshed.refresh };
      accessToken = refreshed.access;
      upstream = await upstreamRequest(request, routePath, accessToken, body);
    } else {
      const response = await makeResponse(upstream);
      clearAuthCookies(response);
      return response;
    }
  }

  const upstreamText = await upstream.text();
  let payload: unknown;
  try {
    payload = upstreamText ? JSON.parse(upstreamText) : undefined;
  } catch {
    payload = undefined;
  }

  const contentType = upstream.headers.get("content-type");
  const headers = new Headers();
  if (contentType) headers.set("Content-Type", contentType);
  const response = new NextResponse(upstreamText || null, {
    status: upstream.status,
    headers,
  });

  if (rotatedTokens) applyAuthCookies(response, rotatedTokens);

  // Never expose access or refresh tokens to browser JavaScript.
  if (
    upstream.ok &&
    (routePath === "token" ||
      routePath === "token/refresh" ||
      routePath === "providers/google/sign-in")
  ) {
    const tokenPayload = payload as
      | { access?: string; refresh?: string; [key: string]: unknown }
      | undefined;
    if (tokenPayload?.access && tokenPayload.refresh) {
      const tokens = { access: tokenPayload.access, refresh: tokenPayload.refresh };
      const sanitized = { ...tokenPayload };
      delete sanitized.access;
      delete sanitized.refresh;
      const safeResponse = NextResponse.json(sanitized, { status: upstream.status });
      applyAuthCookies(safeResponse, tokens);
      return safeResponse;
    }
  }

  if (routePath === "logout" || (routePath === "token/refresh" && !upstream.ok)) {
    clearAuthCookies(response);
  }
  return response;
}

export const GET = handler;
export const POST = handler;
export const PATCH = handler;
export const PUT = handler;
export const DELETE = handler;

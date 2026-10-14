import { NextRequest, NextResponse } from "next/server";

type RouteContext = { params: Promise<{ path: string[] }> };

const ACCESS_COOKIE = "divs_access";
const REFRESH_COOKIE = "divs_refresh";
const ACCESS_MAX_AGE = 15 * 60;
const REFRESH_MAX_AGE = 7 * 24 * 60 * 60;

function apiBaseUrl() {
  return (
    process.env.DIVS_API_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    "http://127.0.0.1:8000/api/v1"
  ).replace(/\/+$/, "");
}

function setTokens(response: NextResponse, tokens: { access: string; refresh: string }) {
  const common = {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/api",
  };
  response.cookies.set(ACCESS_COOKIE, tokens.access, { ...common, maxAge: ACCESS_MAX_AGE });
  response.cookies.set(REFRESH_COOKIE, tokens.refresh, { ...common, maxAge: REFRESH_MAX_AGE });
}

function clearTokens(response: NextResponse) {
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

async function sendUpstream(
  request: NextRequest,
  path: string,
  accessToken: string | undefined,
  body: BodyInit | undefined,
) {
  const headers = new Headers({ Accept: "application/json" });
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("Content-Type", contentType);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  return fetch(`${apiBaseUrl()}/${path}/${request.nextUrl.search}`, {
    method: request.method,
    headers,
    body: request.method === "GET" || request.method === "HEAD" ? undefined : body,
    cache: "no-store",
    redirect: "manual",
  });
}

async function toResponse(upstream: Response) {
  const headers = new Headers();
  for (const name of ["content-type", "content-disposition", "cache-control"]) {
    const value = upstream.headers.get(name);
    if (value) headers.set(name, value);
  }
  const bytes = await upstream.arrayBuffer();
  return new NextResponse(bytes.byteLength ? bytes : null, {
    status: upstream.status,
    headers,
  });
}

async function handler(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  if (!path.length || path.some((part) => !/^[A-Za-z0-9_-]+$/.test(part))) {
    return NextResponse.json({ detail: "Invalid API route." }, { status: 400 });
  }

  const routePath = path.join("/");
  const body: BodyInit | undefined =
    request.method === "GET" || request.method === "HEAD"
      ? undefined
      : await request.arrayBuffer();
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;
  let accessToken = request.cookies.get(ACCESS_COOKIE)?.value;
  const tokenlessRoutes = new Set([
    "auth/register",
    "auth/token",
    "auth/verification/request",
    "auth/verification/confirm",
    "auth/password-reset/request",
    "auth/password-reset/confirm",
    "auth/providers/google",
    "auth/providers/phone",
  ]);
  let upstream: Response;
  if (routePath === "auth/token/refresh" && request.method === "POST") {
    if (!refreshToken) {
      const response = NextResponse.json({ detail: "No active refresh session." }, { status: 401 });
      clearTokens(response);
      return response;
    }
    upstream = await fetch(`${apiBaseUrl()}/auth/token/refresh/`, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: refreshToken }),
      cache: "no-store",
    });
  } else {
    upstream = await sendUpstream(request, routePath, tokenlessRoutes.has(routePath) || routePath.startsWith("discovery/") ? undefined : accessToken, body);
  }
  let rotatedTokens: { access: string; refresh: string } | undefined;

  // Authentication and other protected API calls share the same server-side session cookies.
  if (
    upstream.status === 401 &&
    refreshToken &&
    !tokenlessRoutes.has(routePath) &&
    !routePath.startsWith("discovery/") &&
    routePath !== "auth/token" &&
    routePath !== "auth/token/refresh"
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
      upstream = await sendUpstream(request, routePath, accessToken, body);
    } else {
      const response = await toResponse(upstream);
      clearTokens(response);
      return response;
    }
  }

  const upstreamCopy = upstream.clone();
  const response = await toResponse(upstream);
  if (rotatedTokens) setTokens(response, rotatedTokens);

  const tokenRoutes = new Set([
    "auth/token",
    "auth/token/refresh",
    "auth/providers/google/sign-in",
  ]);
  if (upstream.ok && tokenRoutes.has(routePath)) {
    const payload = (await upstreamCopy.json().catch(() => null)) as
      | { access?: string; refresh?: string; [key: string]: unknown }
      | null;
    if (payload?.access && payload.refresh) {
      const sanitized = { ...payload };
      delete sanitized.access;
      delete sanitized.refresh;
      const safeResponse = NextResponse.json(sanitized, { status: upstream.status });
      setTokens(safeResponse, { access: payload.access, refresh: payload.refresh });
      return safeResponse;
    }
  }

  if (
    routePath === "auth/logout" ||
    (routePath === "auth/token/refresh" && !upstream.ok) ||
    (upstream.status === 401 && refreshToken)
  ) {
    clearTokens(response);
  }
  return response;
}

export const GET = handler;
export const POST = handler;
export const PATCH = handler;
export const PUT = handler;
export const DELETE = handler;

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
  const secure = process.env.NODE_ENV === "production";
  const common = {
    httpOnly: true,
    secure,
    sameSite: "lax" as const,
    path: "/api/auth",
  };
  response.cookies.set(ACCESS_COOKIE, tokens.access, {
    ...common,
    maxAge: ACCESS_MAX_AGE,
  });
  response.cookies.set(REFRESH_COOKIE, tokens.refresh, {
    ...common,
    maxAge: REFRESH_MAX_AGE,
  });
}

function clearAuthCookies(response: NextResponse) {
  const secure = process.env.NODE_ENV === "production";
  for (const name of [ACCESS_COOKIE, REFRESH_COOKIE]) {
    response.cookies.set(name, "", {
      httpOnly: true,
      secure,
      sameSite: "lax",
      path: "/api/auth",
      maxAge: 0,
    });
  }
}

async function upstreamRequest(
  request: NextRequest,
  routePath: string,
  accessToken?: string,
  overrideBody?: string,
) {
  const url = `${apiBaseUrl()}/auth/${routePath}/${request.nextUrl.search}`;
  const headers = new Headers({ Accept: "application/json" });
  const incomingContentType = request.headers.get("content-type");
  if (incomingContentType) headers.set("Content-Type", incomingContentType);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);

  let body: string | undefined = overrideBody;
  if (body === undefined && request.method !== "GET" && request.method !== "HEAD") {
    body = await request.text();
  }

  return fetch(url, {
    method: request.method,
    headers,
    body,
    cache: "no-store",
    redirect: "manual",
  });
}

async function handler(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  if (!path.length || path.some((part) => !/^[A-Za-z0-9_-]+$/.test(part))) {
    return NextResponse.json({ detail: "Invalid authentication route." }, { status: 400 });
  }

  const routePath = path.join("/");
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;
  let accessToken = request.cookies.get(ACCESS_COOKIE)?.value;
  let upstream: Response;

  if (routePath === "token/refresh" && request.method === "POST") {
    if (!refreshToken) {
      const response = NextResponse.json({ detail: "No active refresh session." }, { status: 401 });
      clearAuthCookies(response);
      return response;
    }
    upstream = await upstreamRequest(
      request,
      routePath,
      undefined,
      JSON.stringify({ refresh: refreshToken }),
    );
  } else {
    upstream = await upstreamRequest(request, routePath, accessToken);
  }

  let rotatedTokens: { access: string; refresh: string } | undefined;
  if (
    routePath === "token/refresh" &&
    upstream.ok
  ) {
    const payload = (await upstream.clone().json().catch(() => null)) as
      | { access?: string; refresh?: string }
      | null;
    if (payload?.access && payload.refresh) {
      rotatedTokens = { access: payload.access, refresh: payload.refresh };
    }
  }

  // Retry an expired access token once using the HttpOnly refresh cookie.
  if (
    upstream.status === 401 &&
    refreshToken &&
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
      upstream = await upstreamRequest(request, routePath, accessToken);
    } else {
      const response = await makeResponse(upstream);
      clearAuthCookies(response);
      return response;
    }
  }

  const response = await makeResponse(upstream);
  if (rotatedTokens) applyAuthCookies(response, rotatedTokens);

  // Tokens are stored only in HttpOnly cookies, never returned to browser JavaScript.
  if (
    upstream.ok &&
    (routePath === "token" || routePath === "token/refresh" || routePath === "providers/google/sign-in")
  ) {
    const payload = (await upstream.clone().json().catch(() => null)) as
      | { access?: string; refresh?: string }
      | null;
    if (payload?.access && payload.refresh) {
      applyAuthCookies(response, { access: payload.access, refresh: payload.refresh });
      const sanitized = { ...payload };
      delete sanitized.access;
      delete sanitized.refresh;
      const safeResponse = NextResponse.json(sanitized, { status: upstream.status });
      // Preserve the rotated/new cookies on the replacement response.
      applyAuthCookies(safeResponse, { access: payload.access, refresh: payload.refresh });
      return safeResponse;
    }
  }

  if (routePath === "logout") clearAuthCookies(response);
  return response;
}

async function makeResponse(upstream: Response): Promise<NextResponse> {
  const text = await upstream.text();
  const contentType = upstream.headers.get("content-type");
  const headers = new Headers();
  if (contentType) headers.set("Content-Type", contentType);
  return new NextResponse(text || null, {
    status: upstream.status,
    headers,
  });
}

export const GET = handler;
export const POST = handler;
export const PATCH = handler;
export const PUT = handler;
export const DELETE = handler;

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly payload?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type ApiRequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const normalizedPath = path.replace(/^\/+/, "");
  const headers = new Headers(options.headers);

  headers.set("Accept", "application/json");

  let body: BodyInit | undefined;
  if (options.body instanceof FormData) {
    body = options.body;
  } else if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.body);
  }

  const response = await fetch(
    `/api/backend/${normalizedPath}`,
    {
      ...options,
      headers,
      body,
      credentials: "same-origin",
    },
  );

  if (!response.ok) {
    const responseText = await response.text();
    let payload: unknown = responseText;

    try {
      payload = responseText ? JSON.parse(responseText) : undefined;
    } catch {
      // Keep the original response text when the server did not return JSON.
    }

    throw new ApiError(
      `API request failed with status ${response.status}.`,
      response.status,
      payload,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

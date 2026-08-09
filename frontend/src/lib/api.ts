const API_BASE_URL = "/api/v1";
const ACCESS_TOKEN_KEY = "rahsepar.access-token";

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  authenticated?: boolean;
}

interface ErrorPayload {
  detail?: string | Array<{ msg?: string }>;
}

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function getAccessToken(): string | null {
  return sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  sessionStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY);
}

function extractErrorMessage(payload: ErrorPayload | null): string {
  if (typeof payload?.detail === "string") {
    return payload.detail;
  }

  if (Array.isArray(payload?.detail)) {
    const messages = payload.detail
      .map((item) => item.msg)
      .filter((message): message is string => Boolean(message));
    if (messages.length > 0) {
      return messages.join("، ");
    }
  }

  return "در ارتباط با سرور مشکلی پیش آمد.";
}

async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { body, authenticated = false, headers, ...requestOptions } = options;
  const requestHeaders = new Headers(headers);

  if (body !== undefined) {
    requestHeaders.set("Content-Type", "application/json");
  }

  if (authenticated) {
    const token = getAccessToken();
    if (!token) {
      throw new ApiError(401, "برای ادامه وارد حساب خود شوید.");
    }
    requestHeaders.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...requestOptions,
      headers: requestHeaders,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "ارتباط با سرور برقرار نشد. دوباره تلاش کنید.");
  }

  if (!response.ok) {
    const payload = (await response
      .json()
      .catch(() => null)) as ErrorPayload | null;
    throw new ApiError(response.status, extractErrorMessage(payload));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const api = {
  get<T>(path: string, authenticated = false): Promise<T> {
    return request<T>(path, { method: "GET", authenticated });
  },
  post<T>(path: string, body: unknown, authenticated = false): Promise<T> {
    return request<T>(path, { method: "POST", body, authenticated });
  },
  delete<T>(path: string, authenticated = false): Promise<T> {
    return request<T>(path, { method: "DELETE", authenticated });
  },
};

export function toQueryString(
  values: Record<string, string | number | undefined>,
): string {
  const parameters = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      parameters.set(key, String(value));
    }
  });
  const query = parameters.toString();
  return query ? `?${query}` : "";
}

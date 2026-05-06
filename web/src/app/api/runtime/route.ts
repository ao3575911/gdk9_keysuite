import { NextResponse } from "next/server";
import { mockRuntime, normalizeRuntimePayload, type RuntimeRequest } from "@/lib/runtime";

export const dynamic = "force-dynamic";

const MAX_TOKENS = 4096;
const MAX_TOKEN_LENGTH = 256;
const TOKEN_PATTERN = /^[^\s\x00-\x1f\x7f]+$/u;

function inputError(message: string, status = 400) {
  return NextResponse.json(
    {
      status: "error",
      state: "INPUT_ERROR",
      buffer: [],
      mode: null,
      outputs: [],
      trace: [],
      error: {
        message,
        type: "InputError",
      },
      cursor: 0,
      source: "mock",
      sourceLabel: "Input validation",
    },
    { status },
  );
}

function validateTokens(body: RuntimeRequest | null): string[] | NextResponse {
  if (!Array.isArray(body?.tokens)) {
    return inputError("Request body must include a tokens array.");
  }

  if (body.tokens.length === 0) {
    return inputError("Enter at least one token.");
  }

  if (body.tokens.length > MAX_TOKENS) {
    return inputError(`Token stream exceeds the ${MAX_TOKENS} token limit.`, 413);
  }

  for (const token of body.tokens) {
    if (typeof token !== "string") {
      return inputError("All tokens must be strings.");
    }
    if (token.length === 0) {
      return inputError("Tokens must be non-empty strings.");
    }
    if (token.length > MAX_TOKEN_LENGTH) {
      return inputError(`Tokens must be ${MAX_TOKEN_LENGTH} characters or fewer.`, 413);
    }
    if (!TOKEN_PATTERN.test(token)) {
      return inputError("Tokens cannot contain whitespace or control characters.");
    }
  }

  return body.tokens;
}

function apiBaseUrl(): string | undefined {
  return process.env.KEYSUITE_API_BASE_URL || process.env.NEXT_PUBLIC_KEYSUITE_API_BASE_URL;
}

function apiHeaders(): HeadersInit {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  const apiKey = process.env.KEYSUITE_API_KEY;
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }
  return headers;
}

export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as RuntimeRequest | null;
  const tokens = validateTokens(body);

  if (tokens instanceof NextResponse) {
    return tokens;
  }

  const baseUrl = apiBaseUrl();
  if (!baseUrl) {
    return NextResponse.json(mockRuntime(tokens));
  }

  try {
    const response = await fetch(`${baseUrl.replace(/\/$/, "")}/v1/process`, {
      method: "POST",
      headers: apiHeaders(),
      body: JSON.stringify({ tokens }),
      cache: "no-store",
    });

    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      return NextResponse.json(
        {
          ...mockRuntime(tokens),
          sourceLabel: `API unavailable (${response.status}); showing demo fallback`,
          error: payload?.error
            ? {
                message: payload.error.message,
                type: payload.error.code,
              }
            : {
                message: `API returned HTTP ${response.status}.`,
                type: "ApiError",
              },
        },
        { status: 200 },
      );
    }

    return NextResponse.json(normalizeRuntimePayload(payload, baseUrl));
  } catch (error) {
    const fallback = mockRuntime(tokens);
    return NextResponse.json({
      ...fallback,
      sourceLabel: "API unavailable; showing demo fallback",
      error:
        fallback.error ??
        ({
          message: error instanceof Error ? error.message : "Unable to reach the KeySuite API.",
          type: "ApiUnavailable",
        } as const),
    });
  }
}

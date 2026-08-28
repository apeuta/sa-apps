import { NextRequest, NextResponse } from "next/server";

/**
 * API Route Proxy — catch-all untuk /api/v1/*
 *
 * Meneruskan semua request ke backend container via Docker network.
 * Ini lebih reliable daripada middleware atau rewrites di standalone mode.
 *
 * Endpoint: /api/v1/[...path]
 * Backend: http://backend:8000/api/v1/[...path]
 */

const BACKEND_URL = process.env.BACKEND_URL || "http://backend:8000";
const FRONTEND_URL = process.env.FRONTEND_URL || "http://localhost:3000";

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, "GET");
}

export async function POST(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, "POST");
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, "PUT");
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, "PATCH");
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, "DELETE");
}

/**
 * Proxy request ke backend container
 */
async function proxyRequest(
  request: NextRequest,
  pathSegments: string[],
  method: string
) {
  const path = pathSegments.join("/");
  const searchParams = request.nextUrl.searchParams.toString();
  const queryString = searchParams ? `?${searchParams}` : "";
  const backendUrl = `${BACKEND_URL}/api/v1/${path}${queryString}`;

  console.log(`[API Proxy] ${method} /api/v1/${path} → ${backendUrl}`);

  try {
    // Build headers — forward semua kecuali host
    const headers = new Headers(request.headers);
    headers.delete("host");
    headers.delete("connection");
    headers.delete("content-length"); // akan di-set ulang oleh fetch

    // Forward request body untuk POST/PUT/PATCH
    const fetchOptions: RequestInit = {
      method,
      headers,
      redirect: "manual",
    };

    if (method !== "GET" && method !== "HEAD") {
      fetchOptions.body = await request.text();
    }

    const response = await fetch(backendUrl, fetchOptions);

    console.log(`[API Proxy] ← ${response.status} ${response.statusText}`);

    // Forward response headers
    const responseHeaders = new Headers();
    response.headers.forEach((value, key) => {
      // Skip hop-by-hop headers
      if (!["transfer-encoding", "connection", "keep-alive"].includes(key.toLowerCase())) {
        responseHeaders.set(key, value);
      }
    });

    // Read response body
    const body = await response.text();

    // Special handling: auth/callback → redirect ke frontend callback page
    // Google OAuth redirect ke /api/v1/auth/callback (API route), bukan
    // frontend page. Jadi kita perlu redirect ke /auth/callback dengan data.
    if (path === "auth/callback") {
      if (response.status === 200) {
        try {
          const data = JSON.parse(body);
          if (data.tokens && data.user) {
            const frontendCallbackUrl = new URL("/auth/callback", FRONTEND_URL);
            frontendCallbackUrl.searchParams.set("access_token", data.tokens.access_token);
            frontendCallbackUrl.searchParams.set("refresh_token", data.tokens.refresh_token);
            frontendCallbackUrl.searchParams.set("user", encodeURIComponent(JSON.stringify(data.user)));
            console.log(`[API Proxy] ← auth/callback sukses, redirect ke /auth/callback`);
            return NextResponse.redirect(frontendCallbackUrl);
          }
        } catch (e) {
          console.error(`[API Proxy] ERROR parsing auth/callback response:`, e);
        }
      } else {
        // Error dari backend (403 domain_not_allowed, dll) → redirect ke login
        let errorCode = "auth_failed";
        try {
          const errData = JSON.parse(body);
          if (response.status === 403) errorCode = "domain_not_allowed";
          else if (errData?.detail) errorCode = errData.detail;
        } catch (e) { /* ignore */ }
        console.log(`[API Proxy] ← auth/callback error ${response.status}, redirect ke /login`);
        return NextResponse.redirect(
          new URL(`/login?error=${errorCode}`, FRONTEND_URL)
        );
      }
    }

    return new NextResponse(body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error(`[API Proxy] ERROR: ${method} /api/v1/${path}`, error);
    return NextResponse.json(
      {
        status: "error",
        message: `Backend tidak tersedia: ${error instanceof Error ? error.message : "Unknown error"}`,
      },
      { status: 502 }
    );
  }
}

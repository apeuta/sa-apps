import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Middleware untuk proxy /api/v1/* ke backend container
 *
 * Karena traffic dari external proxy (HTTPS) langsung ke frontend container,
 * kita perlu proxy API request dari dalam Next.js sendiri.
 * Backend container accessible via Docker network hostname "backend:8000".
 */
export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Hanya intercept request ke /api/v1/*
  if (!pathname.startsWith("/api/v1/")) {
    return NextResponse.next();
  }

  // Proxy ke backend container
  const backendUrl = `http://backend:8000${pathname}${request.nextUrl.search}`;

  try {
    const response = await fetch(backendUrl, {
      method: request.method,
      headers: request.headers,
      body: request.method !== "GET" && request.method !== "HEAD"
        ? await request.text()
        : undefined,
    });

    // Forward response dari backend ke client
    const responseHeaders = new Headers(response.headers);
    return new NextResponse(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error(`Middleware proxy error: ${request.method} ${pathname} → ${backendUrl}`, error);
    return NextResponse.json(
      { status: "error", message: "Backend tidak tersedia" },
      { status: 502 }
    );
  }
}

export const config = {
  matcher: "/api/v1/:path*",
};

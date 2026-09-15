import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Only intercept /api/ requests
  if (request.nextUrl.pathname.startsWith('/api/')) {
    // This runs completely dynamically at runtime per-request!
    // Safe for "Build Once, Run Anywhere" (Docker vs K8s)
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    // Construct the destination URL
    const targetUrl = new URL(request.nextUrl.pathname + request.nextUrl.search, backendUrl);
    
    // Rewrite acts as a transparent reverse proxy
    return NextResponse.rewrite(targetUrl);
  }
}

export const config = {
  matcher: '/api/:path*',
};

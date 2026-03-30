import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',

  // Proxy all /api/* requests server-side to the backend.
  // Browser only ever talks to the frontend host — no CORS, no localhost issues.
  // BACKEND_URL is set at runtime via K8s ConfigMap (not baked at build time).
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;

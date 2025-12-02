import type { NextConfig } from "next";

const csp = [
  "default-src 'self'",
  // Allow Next dev tooling (eval/inline) and scripts from https sources.
  "script-src 'self' 'unsafe-eval' 'unsafe-inline' https:",
  "style-src 'self' 'unsafe-inline' https:",
  "img-src 'self' data: https:",
  // Clerk + API calls + dev websocket
  "connect-src 'self' https: http://localhost:* ws://localhost:*",
  "font-src 'self' data: https:",
  "frame-src https: http://localhost:*",
  // Allow workers for Clerk
  "worker-src 'self' blob:",
].join("; ");

const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "Content-Security-Policy",
            value: csp,
          },
        ],
      },
    ];
  },
};

export default nextConfig;

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone só para Docker (EasyPanel/Render). Vercel usa deploy nativo.
  ...(process.env.VERCEL ? {} : { output: "standalone" }),
};

export default nextConfig;

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  // Em desenvolvimento cada ginásio é servido em <slug>.localhost:3000.
  allowedDevOrigins: ["*.localhost"],
};

export default nextConfig;

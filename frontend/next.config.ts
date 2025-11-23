import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Empty turbopack config to silence warning
  turbopack: {},
  
  webpack: (config, { isServer }) => {
    // Exclude test files from production build
    config.module = config.module || {};
    config.module.rules = config.module.rules || [];
    
    config.module.rules.push({
      test: /\.test\.(js|ts|tsx)$/,
      loader: 'ignore-loader'
    });

    // Ignore problematic test dependencies
    config.resolve = config.resolve || {};
    config.resolve.alias = config.resolve.alias || {};
    config.resolve.alias = {
      ...config.resolve.alias,
      'why-is-node-running': false,
      'tap': false,
    };

    return config;
  },
};

export default nextConfig;

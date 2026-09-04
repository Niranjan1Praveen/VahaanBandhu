import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  // This project writes JSX inside .js files (Next.js permits it). Vite 7 uses
  // oxc as its transformer, and oxc does not enable JSX parsing for .js unless
  // told to -- otherwise every page fails with "JSX syntax is disabled".
  oxc: {
    lang: "jsx",
    jsx: { runtime: "automatic" },
  },
  plugins: [react({ include: /\.(js|jsx)$/ })],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.js"],
    // These pages await several parallel fetches before settling; the 1000ms
    // default for findBy* is marginal and produced flaky "element not found".
    testTimeout: 15000,
    include: ["src/**/*.test.{js,jsx}"],
  },
});

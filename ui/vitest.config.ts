import react from "@vitejs/plugin-react-swc";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [
    react(),
  ],
  test: {
    environment: "happy-dom",
    setupFiles: ["./vitest.setup.ts"],
    coverage: {
      provider: "istanbul",
      enabled: true,
      exclude: [
        "node_modules",
        "dist",
        "coverage",
        ".eslintrc.cjs",
        "vite.config.ts",
        "vite.config-explorer.ts",
        "vite.common.ts",
        "src/tool/wasm_exec.js",
        "src/schema/schema.ts",
      ],
    },
    reporters: ["junit", "default", "github-actions"],
    outputFile: {
      junit: "test-results.xml",
    },
  },
});

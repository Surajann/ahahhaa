import { defineConfig } from "vite";

export default defineConfig({
  server: { port: 1420, strictPort: true },
  envPrefix: ["VITE_"],
  build: { target: "esnext" },
  test: {
    environment: "jsdom",
    globals: true,
    fakeTimers: true,
    include: ["tests/**/*.test.ts"]
  }
});

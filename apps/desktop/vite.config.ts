import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  root: "ui",
  clearScreen: false,
  build: { outDir: "dist", emptyOutDir: true },
  server: { strictPort: true },
});

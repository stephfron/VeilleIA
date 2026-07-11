import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Le backend FastAPI (uvicorn api.main:app --port 8000) sert /api/* ;
// en dev Vite proxifie pour éviter tout souci CORS.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});

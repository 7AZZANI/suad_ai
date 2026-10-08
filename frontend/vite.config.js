import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// The API base URL is configurable via VITE_API_BASE_URL (.env).
export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        proxy: {
            "/api": "http://localhost:8000",
            "/health": "http://localhost:8000",
            "/ready": "http://localhost:8000",
        },
    },
});

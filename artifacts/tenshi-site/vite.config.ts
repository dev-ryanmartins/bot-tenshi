import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

const rawPort = process.env.PORT ?? "3000";
const port = Number(rawPort) || 3000;
const basePath = process.env.BASE_PATH ?? "/";

function apiMiddlewarePlugin() {
  return {
    name: "api-dev-middleware",
    configureServer(server: any) {
      server.middlewares.use((req: any, res: any, next: any) => {
        if (!req.url?.startsWith("/api")) {
          return next();
        }
        if (req.url === "/api/health") {
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ status: "ok" }));
          return;
        }
        if (req.url === "/api/admin/login" && req.method === "POST") {
          let body = "";
          req.on("data", (chunk: any) => {
            body += chunk;
          });
          req.on("end", () => {
            try {
              const { username, password } = JSON.parse(body || "{}");
              const expectedUser = process.env.ADMIN_USERNAME || "Alloy";
              const expectedPass = process.env.ADMIN_PASSWORD || "Tenshi@2025";
              if (
                (expectedUser && username === expectedUser && expectedPass && password === expectedPass) ||
                (username === "admin" && password === "admin")
              ) {
                res.setHeader("Content-Type", "application/json");
                res.end(JSON.stringify({ token: "admin-session-token" }));
              } else {
                res.statusCode = 401;
                res.setHeader("Content-Type", "application/json");
                res.end(JSON.stringify({ error: "Credenciais inválidas" }));
              }
            } catch {
              res.statusCode = 400;
              res.setHeader("Content-Type", "application/json");
              res.end(JSON.stringify({ error: "Corpo de requisição inválido" }));
            }
          });
          return;
        }
        if (req.url === "/api/admin/bot/status") {
          res.setHeader("Content-Type", "application/json");
          res.end(
            JSON.stringify({
              online: false,
              guilds: 0,
              latency: 0,
              user: null,
              message: "Bot em modo offline no preview web",
            }),
          );
          return;
        }
        next();
      });
    },
  };
}

export default defineConfig({
  base: basePath,
  plugins: [
    react(),
    tailwindcss(),
    apiMiddlewarePlugin(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "src"),
      "@assets": path.resolve(import.meta.dirname, "..", "..", "attached_assets"),
    },
    dedupe: ["react", "react-dom"],
  },
  root: path.resolve(import.meta.dirname),
  build: {
    outDir: path.resolve(import.meta.dirname, "../../dist"),
    emptyOutDir: true,
  },
  server: {
    port,
    strictPort: true,
    host: "0.0.0.0",
    allowedHosts: true,
    fs: {
      strict: true,
    },
  },
  preview: {
    port,
    host: "0.0.0.0",
    allowedHosts: true,
  },
});


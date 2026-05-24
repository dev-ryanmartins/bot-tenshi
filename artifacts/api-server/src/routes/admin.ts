import { Router } from "express";
import crypto from "crypto";

const router = Router();

function generateToken(username: string, password: string): string {
  const secret = process.env.ADMIN_SECRET ?? "fallback";
  return crypto.createHmac("sha256", secret).update(`${username}:${password}`).digest("hex");
}

function verifyBearer(authHeader: string | undefined): boolean {
  if (!authHeader?.startsWith("Bearer ")) return false;
  const token = authHeader.slice(7);
  const expected = generateToken(
    process.env.ADMIN_USERNAME ?? "",
    process.env.ADMIN_PASSWORD ?? ""
  );
  return token === expected;
}

router.post("/admin/login", (req, res) => {
  const { username, password } = req.body as { username: string; password: string };
  const expectedUser = process.env.ADMIN_USERNAME ?? "";
  const expectedPass = process.env.ADMIN_PASSWORD ?? "";
  if (username !== expectedUser || password !== expectedPass) {
    res.status(401).json({ error: "Credenciais inválidas" });
    return;
  }
  const token = generateToken(username, password);
  res.json({ token });
});

router.get("/admin/bot/status", async (req, res) => {
  if (!verifyBearer(req.headers.authorization)) {
    res.status(401).json({ error: "Não autorizado" });
    return;
  }
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);
    const r = await fetch("http://localhost:8090/status", { signal: controller.signal });
    clearTimeout(timeout);
    const data = await r.json();
    res.json(data);
  } catch {
    res.json({ online: false, guilds: 0, latency: 0, user: null });
  }
});

router.post("/admin/bot/reconnect", async (req, res) => {
  if (!verifyBearer(req.headers.authorization)) {
    res.status(401).json({ error: "Não autorizado" });
    return;
  }
  try {
    const secret = process.env.ADMIN_SECRET ?? "";
    const r = await fetch("http://localhost:8090/reconnect", {
      method: "POST",
      headers: { "X-Admin-Token": secret.slice(0, 32) },
    });
    const data = await r.json();
    res.json(data);
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
});

export default router;

import { Router } from "express";
import crypto from "crypto";
import { readFile } from "node:fs/promises";
import path from "node:path";

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
    process.env.ADMIN_PASSWORD ?? "",
  );
  return token === expected;
}

async function readBotStatus() {
  const statusPath = process.env.TENSHI_BOT_STATUS_FILE
    ?? path.resolve(process.cwd(), "artifacts", "tenshi-bot", "data", "status.json");
  const raw = await readFile(statusPath, "utf-8");
  const data = JSON.parse(raw);
  const updatedAt = Date.parse(data.updated_at ?? "");
  const stale = Number.isNaN(updatedAt) || Date.now() - updatedAt > 45_000;

  return {
    online: Boolean(data.online) && !stale,
    guilds: Number(data.guilds ?? 0),
    latency: Number(data.latency ?? 0),
    user: data.user ?? null,
  };
}

router.post("/admin/login", (req, res) => {
  const { username, password } = req.body as { username: string; password: string };
  const expectedUser = process.env.ADMIN_USERNAME ?? "";
  const expectedPass = process.env.ADMIN_PASSWORD ?? "";

  if (username !== expectedUser || password !== expectedPass) {
    res.status(401).json({ error: "Credenciais invalidas" });
    return;
  }

  res.json({ token: generateToken(username, password) });
});

router.get("/admin/bot/status", async (req, res) => {
  if (!verifyBearer(req.headers.authorization)) {
    res.status(401).json({ error: "Nao autorizado" });
    return;
  }

  try {
    res.json(await readBotStatus());
  } catch {
    res.json({ online: false, guilds: 0, latency: 0, user: null });
  }
});

router.post("/admin/bot/reconnect", (req, res) => {
  if (!verifyBearer(req.headers.authorization)) {
    res.status(401).json({ error: "Nao autorizado" });
    return;
  }

  res.status(410).json({
    error: "Reconexao pelo site foi removida. Use o supervisor do processo do bot.",
  });
});

export default router;

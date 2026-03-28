import { createHmac, timingSafeEqual } from "crypto";
import { nanoid } from "nanoid";
import { pruneExpiredTokens, tokenStore } from "../store.js";

function getEnv(name: string): string | null {
  const value = process.env[name];
  return value && value.trim() ? value : null;
}

function validateRedirect(rawRedirect: string): { ok: true; redirect: string; port: number } | { ok: false } {
  let url: URL;
  try {
    url = new URL(rawRedirect);
  } catch {
    return { ok: false };
  }

  if (url.protocol !== "http:") return { ok: false };
  if (url.hostname !== "localhost" && url.hostname !== "127.0.0.1") return { ok: false };
  if (!url.port) return { ok: false };
  const port = Number(url.port);
  if (!Number.isInteger(port) || port < 1024 || port > 65535) return { ok: false };

  return { ok: true, redirect: url.toString(), port };
}

function decodeState(rawState: string): { redirect: string; timestamp: number; hmac: string } | null {
  try {
    const decoded = Buffer.from(rawState, "base64").toString("utf-8");
    const parsed = JSON.parse(decoded) as { redirect: string; timestamp: number; hmac: string };
    if (!parsed || typeof parsed.redirect !== "string" || typeof parsed.timestamp !== "number" || typeof parsed.hmac !== "string") {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function verifyHmac(redirect: string, timestamp: number, provided: string, secret: string): boolean {
  const expected = createHmac("sha256", secret).update(redirect + String(timestamp)).digest("hex");
  if (expected.length !== provided.length) return false;
  return timingSafeEqual(Buffer.from(expected, "hex"), Buffer.from(provided, "hex"));
}

async function exchangeCodeForToken(code: string, clientId: string, clientSecret: string): Promise<Record<string, unknown>> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10_000);

  try {
    const body = new URLSearchParams({
      code,
      client_id: clientId,
      client_secret: clientSecret,
      redirect_uri: "https://jenil-otpilot.vercel.app/api/auth/callback",
      grant_type: "authorization_code",
    });

    const response = await fetch("https://oauth2.googleapis.com/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
      signal: controller.signal,
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Token exchange failed: ${response.status} ${text}`);
    }

    return (await response.json()) as Record<string, unknown>;
  } finally {
    clearTimeout(timeout);
  }
}

export default async function handler(req: any, res: any): Promise<void> {
  if (req.method && req.method !== "GET") {
    res.statusCode = 405;
    res.end("Method Not Allowed");
    return;
  }

  const clientId = getEnv("GOOGLE_CLIENT_ID");
  const clientSecret = getEnv("GOOGLE_CLIENT_SECRET");
  const hmacSecret = getEnv("HMAC_SECRET");

  if (!clientId || !clientSecret || !hmacSecret) {
    res.statusCode = 500;
    res.end("Missing required environment variables.");
    return;
  }

  const code = typeof req.query?.code === "string" ? req.query.code : null;
  const state = typeof req.query?.state === "string" ? req.query.state : null;

  if (!code || !state) {
    res.statusCode = 400;
    res.end("Missing code or state.");
    return;
  }

  const decodedState = decodeState(state);
  if (!decodedState) {
    res.statusCode = 400;
    res.end("Invalid state.");
    return;
  }

  const { redirect, timestamp, hmac } = decodedState;
  const validated = validateRedirect(redirect);
  if (!validated.ok) {
    res.statusCode = 400;
    res.end("Invalid redirect in state.");
    return;
  }

  const now = Date.now();
  if (now - timestamp > 5 * 60 * 1000) {
    res.statusCode = 400;
    res.end("State expired.");
    return;
  }

  if (!verifyHmac(redirect, timestamp, hmac, hmacSecret)) {
    res.statusCode = 400;
    res.end("Invalid state signature.");
    return;
  }

  try {
    const tokenJson = await exchangeCodeForToken(code, clientId, clientSecret);

    pruneExpiredTokens(now);
    const oneTimeCode = nanoid(32);
    tokenStore.set(oneTimeCode, {
      tokenJson,
      expiresAt: now + 60_000,
    });

    const redirectUrl = new URL(`http://localhost:${validated.port}`);
    redirectUrl.searchParams.set("code", oneTimeCode);

    res.statusCode = 302;
    res.setHeader("Location", redirectUrl.toString());
    res.end();
  } catch (error) {
    res.statusCode = 500;
    res.end("Error exchanging token.");
  }
}

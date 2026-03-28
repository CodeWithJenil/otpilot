import { createHmac } from "crypto";

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

export default function handler(req: any, res: any): void {
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

  const redirectParam = typeof req.query?.redirect === "string" ? req.query.redirect : null;
  if (!redirectParam) {
    res.statusCode = 400;
    res.end("Missing redirect parameter.");
    return;
  }

  const validated = validateRedirect(redirectParam);
  if (!validated.ok) {
    res.statusCode = 400;
    res.end("Invalid redirect parameter.");
    return;
  }

  const redirect = validated.redirect;
  const timestamp = Date.now();
  const hmac = createHmac("sha256", hmacSecret).update(redirect + String(timestamp)).digest("hex");

  const statePayload = { redirect, timestamp, hmac };
  const state = Buffer.from(JSON.stringify(statePayload)).toString("base64");

  const googleAuthUrl = new URL("https://accounts.google.com/o/oauth2/v2/auth");
  googleAuthUrl.searchParams.set("client_id", clientId);
  googleAuthUrl.searchParams.set("redirect_uri", "https://jenil-otpilot.vercel.app/api/auth/callback");
  googleAuthUrl.searchParams.set("response_type", "code");
  googleAuthUrl.searchParams.set("scope", "https://www.googleapis.com/auth/gmail.readonly");
  googleAuthUrl.searchParams.set("access_type", "offline");
  googleAuthUrl.searchParams.set("prompt", "consent");
  googleAuthUrl.searchParams.set("state", state);

  res.statusCode = 302;
  res.setHeader("Location", googleAuthUrl.toString());
  res.end();
}

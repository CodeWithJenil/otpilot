import { pruneExpiredTokens, tokenStore } from "../store.js";

export default function handler(req: any, res: any): void {
  if (req.method && req.method !== "GET") {
    res.statusCode = 405;
    res.end("Method Not Allowed");
    return;
  }

  const code = typeof req.query?.code === "string" ? req.query.code : null;
  if (!code) {
    res.statusCode = 400;
    res.end("Missing code parameter.");
    return;
  }

  const now = Date.now();
  pruneExpiredTokens(now);

  const entry = tokenStore.get(code);
  if (!entry || entry.expiresAt <= now) {
    tokenStore.delete(code);
    res.statusCode = 400;
    res.end("Invalid or expired code.");
    return;
  }

  tokenStore.delete(code);
  res.statusCode = 200;
  res.setHeader("Content-Type", "application/json");
  res.end(JSON.stringify(entry.tokenJson));
}

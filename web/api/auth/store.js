export const sessionStore = new Map();

export function putSessionToken(sessionKey, providerToken, ttlMs = 2 * 60_000) {
  sessionStore.set(sessionKey, {
    providerToken,
    expiresAt: Date.now() + ttlMs,
  });
}

export function takeSessionToken(sessionKey) {
  const entry = sessionStore.get(sessionKey);
  if (!entry) return null;
  if (entry.expiresAt <= Date.now()) {
    sessionStore.delete(sessionKey);
    return null;
  }
  sessionStore.delete(sessionKey);
  return entry.providerToken;
}

export function pruneExpired() {
  const now = Date.now();
  for (const [key, entry] of sessionStore.entries()) {
    if (entry.expiresAt <= now) sessionStore.delete(key);
  }
}

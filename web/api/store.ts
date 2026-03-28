export type TokenEntry = {
  tokenJson: Record<string, unknown>;
  expiresAt: number;
};

export const tokenStore = new Map<string, TokenEntry>();

export function pruneExpiredTokens(now: number = Date.now()): void {
  for (const [code, entry] of tokenStore.entries()) {
    if (entry.expiresAt <= now) {
      tokenStore.delete(code);
    }
  }
}

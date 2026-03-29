const { createSupabaseAdminClient } = require("../lib/supabase.js");

const OTP_SESSIONS_TABLE = "otp_sessions";

async function putSessionToken(sessionKey, providerToken, ttlMs = 2 * 60_000) {
  const supabase = createSupabaseAdminClient();
  const expiresAt = new Date(Date.now() + ttlMs).toISOString();

  const { error } = await supabase.from(OTP_SESSIONS_TABLE).upsert(
    {
      session_key: sessionKey,
      provider_token: providerToken,
      expires_at: expiresAt,
    },
    { onConflict: "session_key" },
  );

  if (error) {
    throw new Error(`Failed to store oauth session: ${error.message}`);
  }
}

async function takeSessionToken(sessionKey) {
  const supabase = createSupabaseAdminClient();

  const { data, error } = await supabase
    .from(OTP_SESSIONS_TABLE)
    .select("provider_token, expires_at")
    .eq("session_key", sessionKey)
    .maybeSingle();

  if (error) {
    throw new Error(`Failed to load oauth session: ${error.message}`);
  }

  if (!data) {
    return null;
  }

  const { error: deleteError } = await supabase.from(OTP_SESSIONS_TABLE).delete().eq("session_key", sessionKey);
  if (deleteError) {
    throw new Error(`Failed to delete oauth session: ${deleteError.message}`);
  }

  if (!data.expires_at || new Date(data.expires_at).getTime() <= Date.now()) {
    return null;
  }

  return data.provider_token || null;
}

async function pruneExpired() {
  const supabase = createSupabaseAdminClient();
  const nowIso = new Date().toISOString();
  const { error } = await supabase.from(OTP_SESSIONS_TABLE).delete().lte("expires_at", nowIso);
  if (error) {
    throw new Error(`Failed to prune expired oauth sessions: ${error.message}`);
  }
}

module.exports = {
  putSessionToken,
  takeSessionToken,
  pruneExpired,
};

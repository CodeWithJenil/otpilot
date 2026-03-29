const { createSupabaseClient } = require("../lib/supabase.js");

module.exports = async function handler(req, res) {
  if (req.method && req.method !== "GET") {
    res.statusCode = 405;
    res.end("Method Not Allowed");
    return;
  }

  const sessionKey = typeof req.query?.session_key === "string" ? req.query.session_key : null;
  if (!sessionKey) {
    res.statusCode = 400;
    res.end("Missing session_key parameter.");
    return;
  }

  try {
    const supabase = createSupabaseClient();
    const redirectTo = `${req.headers["x-forwarded-proto"] || "https"}://${req.headers.host}/api/auth/callback?session_key=${encodeURIComponent(sessionKey)}`;

    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        scopes: "https://www.googleapis.com/auth/gmail.readonly",
        queryParams: { access_type: "offline", prompt: "consent" },
        redirectTo,
      },
    });

    if (error || !data?.url) {
      res.statusCode = 500;
      res.end(`Could not initiate OAuth flow: ${error?.message || "No URL returned"}`);
      return;
    }

    res.statusCode = 302;
    res.setHeader("Location", data.url);
    res.end();
  } catch (error) {
    res.statusCode = 500;
    res.end(`Unexpected auth error: ${error instanceof Error ? error.message : "Unknown error"}`);
  }
};

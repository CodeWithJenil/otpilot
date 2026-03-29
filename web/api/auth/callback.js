const { createSupabaseClient } = require("../lib/supabase.js");
const { putSessionToken, pruneExpired } = require("./store.js");

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

  const providerTokenFromQuery = typeof req.query?.provider_token === "string" ? req.query.provider_token : null;
  let providerToken = providerTokenFromQuery;

  try {
    const supabase = createSupabaseClient();
    const code = typeof req.query?.code === "string" ? req.query.code : null;

    if (!providerToken && code) {
      const { data, error } = await supabase.auth.exchangeCodeForSession(code);
      if (!error) {
        providerToken = data?.session?.provider_token ?? null;
      }
    }

    if (!providerToken) {
      const accessToken = typeof req.query?.access_token === "string" ? req.query.access_token : null;
      const refreshToken = typeof req.query?.refresh_token === "string" ? req.query.refresh_token : null;

      if (accessToken && refreshToken) {
        const { data, error } = await supabase.auth.setSession({ access_token: accessToken, refresh_token: refreshToken });
        if (!error) {
          providerToken = data?.session?.provider_token ?? null;
        }
      }
    }

    if (providerToken) {
      await pruneExpired();
      await putSessionToken(sessionKey, providerToken);
      res.statusCode = 200;
      res.setHeader("Content-Type", "text/html; charset=utf-8");
      res.end("<h1>OTPilot connected</h1><p>You can close this tab and return to your terminal.</p>");
      return;
    }

    res.statusCode = 200;
    res.setHeader("Content-Type", "text/html; charset=utf-8");
    res.end(`<!doctype html><html><body><script>
      const fragment = new URLSearchParams(window.location.hash.slice(1));
      const params = new URLSearchParams(window.location.search);
      for (const [k, v] of fragment.entries()) params.set(k, v);
      if (fragment.toString()) {
        window.location.replace(window.location.pathname + '?' + params.toString());
      } else {
        document.body.innerHTML = '<h1>Authorization incomplete</h1><p>No provider token found.</p>';
      }
    </script></body></html>`);
  } catch (error) {
    res.statusCode = 500;
    res.end(`Auth callback failed: ${error instanceof Error ? error.message : "Unknown error"}`);
  }
};

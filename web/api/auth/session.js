const { pruneExpired, takeSessionToken } = require("./store.js");

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

  await pruneExpired();
  const providerToken = await takeSessionToken(sessionKey);

  if (!providerToken) {
    res.statusCode = 202;
    res.setHeader("Content-Type", "application/json");
    res.end(JSON.stringify({ status: "pending" }));
    return;
  }

  res.statusCode = 200;
  res.setHeader("Content-Type", "application/json");
  res.end(JSON.stringify({ provider_token: providerToken }));
};

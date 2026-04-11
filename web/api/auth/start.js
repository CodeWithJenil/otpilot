module.exports = async function handler(req, res) {
  res.statusCode = 410;
  res.setHeader("Content-Type", "application/json");
  res.end(JSON.stringify({ error: "Deprecated. Update OTPilot to v3.0+" }));
};

const PYPI_URL = "https://pypistats.org/api/packages/otpilot/recent";
const GITHUB_URL = "https://api.github.com/repos/CodeWithJenil/otpilot";

async function fetchJson(url, init) {
  const response = await fetch(url, init);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Cache-Control", "s-maxage=3600");

  if (req.method && req.method !== "GET") {
    res.statusCode = 405;
    res.end("Method Not Allowed");
    return;
  }

  const result = {
    downloads: {
      last_day: 0,
      last_week: 0,
      last_month: 0,
    },
    github: {
      stars: 0,
      forks: 0,
    },
    pypi_url: "https://pypi.org/project/otpilot",
    github_url: "https://github.com/CodeWithJenil/otpilot",
  };

  const [pypiResult, githubResult] = await Promise.allSettled([
    fetchJson(PYPI_URL),
    fetchJson(GITHUB_URL, {
      headers: {
        "User-Agent": "otpilot-stats",
        Accept: "application/vnd.github+json",
      },
    }),
  ]);

  if (pypiResult.status === "fulfilled") {
    const data = pypiResult.value?.data;
    if (data && typeof data === "object") {
      result.downloads.last_day = Number(data.last_day) || 0;
      result.downloads.last_week = Number(data.last_week) || 0;
      result.downloads.last_month = Number(data.last_month) || 0;
    }
  }

  if (githubResult.status === "fulfilled") {
    const data = githubResult.value;
    if (data && typeof data === "object") {
      result.github.stars = Number(data.stargazers_count) || 0;
      result.github.forks = Number(data.forks_count) || 0;
    }
  }

  res.statusCode = 200;
  res.setHeader("Content-Type", "application/json");
  res.end(JSON.stringify(result));
}

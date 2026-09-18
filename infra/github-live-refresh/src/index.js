// GitHub profile-art live refresher.
//
// Deploy as a Cloudflare Worker with the Cron Trigger below. Every 5 minutes
// it POSTs a workflow_dispatch for every repo in LIVE_REPOS, which runs each
// repo's live-refresh workflow (re-scrapes data / bumps the README day
// counter and auto-commits).
//
// GitHub's own `on: schedule` can't be trusted for 5-min cadence (best-effort,
// throttled), so we drive it from here instead, which fires on time.
//
// Needs one secret (set with `wrangler secret put`):
//   GH_TOKEN   - a full-scope PAT (repo + workflow), owner of all repos.
//   GH_OWNER   - account that owns all the repos, default in wrangler.toml.

// ponytail: one Worker, one endpoint, no framework. Add retries/logging/queue
//   only if GitHub API ever errors on you; the next 5-min tick re-fires anyway.

const WORKFLOWS = {
  imzyrix: "update-profile-art.yml",
  zyrixanime: "live-tick.yml",
  "TBS-panel": "live-tick.yml",
  "TBS-docs": "live-tick.yml",
  Ren: "live-tick.yml",
};

export default {
  async scheduled(event, env, ctx) {
    for (const repo of Object.keys(WORKFLOWS)) {
      const r = repo.trim();
      const wf = WORKFLOWS[r] || "live-tick.yml";
      const res = await fetch(
        `https://api.github.com/repos/${env.GH_OWNER}/${r}/actions/workflows/${wf}/dispatches`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${env.GH_TOKEN}`,
            Accept: "application/vnd.github+json",
            "User-Agent": "imzyrix-live-refresh",
          },
          body: JSON.stringify({ ref: "main" }),
        }
      );
      console.log(`dispatch ${r}/${wf} -> ${res.status} ${res.statusText}`);
    }
  },
};

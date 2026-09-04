// GitHub profile-art live refresher.
//
// Deploy as a Cloudflare Worker with the Cron Trigger below. Every 5 minutes
// it POSTs a workflow_dispatch that runs .github/workflows/update-profile-art.yml,
// which re-scrapes contributions + Discord presence, re-renders the SVGs, and
// auto-commits (the refresh commit message includes the live contribution count).
//
// GitHub's own `on: schedule` can't be trusted for 5-min cadence (best-effort,
// throttled), so we drive it from here instead, which fires on time.
//
// Needs two secrets (set with `wrangler secret put`):
//   GH_TOKEN   - a fine-grained PAT, scoped to this repo ONLY, with
//                "Actions: Read and write" (workflow) permission.
//   GH_OWNER   - repo owner, default in wrangler.toml but overridable.
// The pattern can be validated with `npx wrangler test` (Vitest last).

// ponytail: one Worker, one endpoint, no framework. Add retries/logging/queue
//   only if GitHub API ever errors on you; the next 5-min tick re-fires anyway.

export default {
  async scheduled(event, env, ctx) {
    const res = await fetch(
      `https://api.github.com/repos/${env.GH_OWNER}/imzyrix/actions/workflows/update-profile-art.yml/dispatches`,
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
    console.log(`dispatch -> ${res.status} ${res.statusText}`);
  },
};

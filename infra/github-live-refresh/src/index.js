// GitHub profile-art live refresher.
//
// Deploy as a Cloudflare Worker with the Cron Trigger below. Every 5 minutes:
//  - imzyrix (public):       POST a workflow_dispatch for update-profile-art.yml
//                            (re-scrapes data + auto-commits; public repos get
//                            unlimited free Actions minutes).
//  - private repos (TICKS):  push the README "Day N + timestamp" tick DIRECTLY
//                            via the Contents API. No GitHub Actions run at all,
//                            so no billable minutes (private Actions minutes
//                            need a paid plan / spending limit).
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
};

const TICKS = ["zyrixanime", "TBS-panel", "TBS-docs", "Ren"];

const TICK_MSG = "chore: live tick [skip ci]";

// btoa/atob aren't UTF-8 safe; GitHub Contents API speaks UTF-8.
const enc = new TextEncoder();
const dec = new TextDecoder();
const b64 = (s) => btoa(String.fromCharCode(...enc.encode(s)));
const unb64 = (s) => dec.decode(Uint8Array.from(atob(s), (c) => c.charCodeAt(0)));

async function gh(env, repo, method, path, body) {
  const res = await fetch(
    `https://api.github.com/repos/${env.GH_OWNER}/${repo}${path}`,
    {
      method,
      headers: {
        Authorization: `Bearer ${env.GH_TOKEN}`,
        Accept: "application/vnd.github.v3+json",
        "User-Agent": "imzyrix-live-refresh",
      },
      body: body ? JSON.stringify(body) : undefined,
    }
  );
  return res;
}

// Ported verbatim from the old live-tick.yml python in the tick repos.
async function tick(env, repo) {
  const now = new Date();
  const today = now.toISOString().slice(0, 10);
  const ts = now.toISOString().slice(0, 19).replace("T", " ") + " UTC";

  let stateFile = await gh(env, repo, "GET", "/contents/.live-day");
  let state = null;
  if (stateFile.status === 200) {
    state = await stateFile.json();
  }
  let day = 0;
  let lastDate = null;
  if (state) {
    const parts = unb64(state.content).trim().split(/\s+/);
    day = parseInt(parts[0]) || 0;
    lastDate = parts.length > 1 ? parts[1] : null;
  }
  if (lastDate !== today) day += 1;

  const block =
    `<!-- LIVE:START -->\n**Day ${day}** &mdash; last refreshed \`${ts}\`\n<!-- LIVE:END -->`;

  let readme = null;
  for (const name of ["README.md", "readme.md", "Readme.md"]) {
    const r = await gh(env, repo, "GET", `/contents/${name}`);
    if (r.status === 200) {
      readme = await r.json();
      break;
    }
  }
  let text = readme ? unb64(readme.content) : "";
  if (text.includes("<!-- LIVE:START -->")) {
    text = text.replace(/<!-- LIVE:START -->[\s\S]*?<!-- LIVE:END -->/, block);
  } else {
    text = text.trimEnd() + "\n\n" + block + "\n";
  }

  const readmePath = readme ? readme.path : "README.md";
  const put = (path, content, sha) =>
    gh(env, repo, "PUT", `/contents/${path}`, {
      message: TICK_MSG,
      content: b64(content),
      ...(sha ? { sha } : {}),
    });

  const readmeRes = await put(readmePath, text, readme ? readme.sha : null);
  console.log(`tick ${repo} ${readmePath} -> ${readmeRes.status} Day ${day} @ ${ts}`);
  if (readmeRes.status >= 400) return;

  const statePut = await put(".live-day", `${day} ${today}\n`, state ? state.sha : null);
  console.log(`tick ${repo} .live-day -> ${statePut.status}`);
}

export default {
  async scheduled(event, env, ctx) {
    for (const repo of Object.keys(WORKFLOWS)) {
      const res = await gh(env, repo, "POST", `/actions/workflows/${WORKFLOWS[repo]}/dispatches`, {
        ref: "main",
      });
      console.log(`dispatch ${repo}/${WORKFLOWS[repo]} -> ${res.status} ${res.statusText}`);
    }
    for (const repo of TICKS) {
      try {
        await tick(env, repo);
      } catch (err) {
        console.log(`tick ${repo} failed: ${err.message}`);
      }
    }
  },
};
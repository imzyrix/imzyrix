"""
Fetch live Discord presence from the public Lanyard API (no auth, no bot token)
and write data/discord.json for the SVG renderer.

Endpoints:
    https://api.lanyard.rest/v1/users/<user_id>

The user must be a member of the Lanyard Discord server for their presence to
be exposed (https://discord.gg/lanyard). Configure the Discord user ID via the
DISCORD_USER_ID environment variable (used by the GitHub Action) or by setting
ID here / in scripts/config.json.

Run by .github/workflows/update-profile-art.yml.
"""
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "..", "data", "discord.json")


def load_id():
    env = os.environ.get("DISCORD_USER_ID")
    if env:
        return env.strip()
    try:
        cfg = json.load(open(os.path.join(HERE, "config.json")))
        if cfg.get("discord_user_id"):
            return str(cfg["discord_user_id"]).strip()
    except (OSError, ValueError):
        pass
    return None


def main():
    user_id = load_id()
    if not user_id:
        print(
            "no Discord user ID set. Put it in DISCORD_USER_ID (CI) or "
            "scripts/config.json (local).",
            file=sys.stderr,
        )
        # write an explicit empty placeholder so the renderer can fall back
        # gracefully instead of failing the whole daily run.
        os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
        json.dump({"configured": False}, open(OUT_PATH, "w"))
        sys.exit(0)

    url = f"https://api.lanyard.rest/v1/users/{user_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "imzyrix-profile/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            payload = json.loads(r.read().decode())
    except Exception as e:
        print(f"lanyard fetch failed ({e}); writing placeholder", file=sys.stderr)
        os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
        json.dump({"configured": False, "error": str(e)}, open(OUT_PATH, "w"))
        sys.exit(0)

    if not payload.get("success"):
        print("lanyard says not success; user may not be in the Lanyard server",
              file=sys.stderr)
        json.dump({"configured": True, "error": "no_presence"},
                  open(OUT_PATH, "w"))
        sys.exit(0)

    data = payload["data"]
    user = data.get("discord_user", {})
    avatar = user.get("avatar") or ""
    avatar_url = (f"https://cdn.discordapp.com/avatars/{user.get('id')}/{avatar}"
                  f".png?size=128") if avatar else \
        "https://cdn.discordapp.com/embed/avatars/0.png"

    out = {
        "configured": True,
        "user_id": user_id,
        "username": user.get("username") or "Discord",
        "display_name": user.get("display_name") or user.get("global_name") or user.get("username") or "Discord",
        "avatar": avatar_url,
        "status": data.get("discord_status", "offline"),
        "active_on_mobile": data.get("active_on_discord_mobile", False),
        "active_on_desktop": data.get("active_on_discord_desktop", False),
        "spotify": data.get("spotify"),
        "listening_to_spotify": data.get("listening_to_spotify", False),
        "activities": data.get("activities", []),
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    json.dump(out, open(OUT_PATH, "w"), indent=2)
    print(f"wrote {OUT_PATH}: {out['username']} is {out['status']}")


if __name__ == "__main__":
    main()

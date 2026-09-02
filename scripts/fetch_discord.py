"""
Fetch live Discord presence from the public Lanyard API (no auth, no bot token)
and write data/discord.json for the SVG renderer, plus download the avatar and
avatar-decoration assets (rasterized to a small static PNG) into data/discord/.

Endpoints:
    presence  -> https://api.lanyard.rest/v1/users/<user_id>
    avatar    -> https://cdn.discordapp.com/avatars/<user_id>/<hash>.png?size=128
    decoration-> https://cdn.discordapp.com/avatar-decoration-presets/<asset>.png
                 (animated APNG; we take a representative static frame + downscale)

The user must be a member of the Lanyard Discord server for their presence to
be exposed (https://discord.gg/lanyard). Configure the Discord user ID via the
DISCORD_USER_ID env var (used by the GH Action) or scripts/config.json.

Run by .github/workflows/update-profile-art.yml.
"""
import base64
import io
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(HERE, "..", "data", "discord.json")
OUT_DIR = os.path.join(HERE, "..", "data", "discord")

UA = {"User-Agent": "imzyrix-profile/1.0"}


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


def http_get(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def rasterize(url, target_size, out_path):
    """Download an (animated) image, take the first frame, fit to target_size."""
    data = http_get(url, binary=True)
    from PIL import Image
    im = Image.open(io.BytesIO(data))
    im.seek(0)
    frame = im.convert("RGBA")
    # ponytail: single static deco frame, not the full APNG animation — for a
    # 96px card ring the difference is invisible; swap to frame compositing if
    # the deco ever needs to stay animated.
    frame.thumbnail((target_size, target_size), Image.LANCZOS)
    frame.save(out_path, "PNG", optimize=True)


def b64(path):
    return base64.b64encode(open(path, "rb").read()).decode()


def main():
    user_id = load_id()
    os.makedirs(OUT_DIR, exist_ok=True)
    if not user_id:
        print("no Discord user ID set; writing placeholder", file=sys.stderr)
        json.dump({"configured": False}, open(OUT_JSON, "w"))
        sys.exit(0)

    try:
        payload = json.loads(http_get(f"https://api.lanyard.rest/v1/users/{user_id}").decode())
    except Exception as e:
        print(f"lanyard fetch failed ({e}); writing placeholder", file=sys.stderr)
        json.dump({"configured": False, "error": str(e)}, open(OUT_JSON, "w"))
        sys.exit(0)

    out = {"configured": False, "error": "no_presence"}
    if not payload.get("success"):
        json.dump(out, open(OUT_JSON, "w"))
        sys.exit(0)

    data = payload["data"]
    du = data.get("discord_user", {})
    avatar_hash = du.get("avatar") or ""

    avatar_url = (f"https://cdn.discordapp.com/avatars/{du.get('id')}/{avatar_hash}"
                  f".png?size=128") if avatar_hash else \
        "https://cdn.discordapp.com/embed/avatars/0.png"
    deco = du.get("avatar_decoration_data") or {}

    # download + rasterize assets
    try:
        rasterize(avatar_url, 128, os.path.join(OUT_DIR, "avatar.png"))
        print("downloaded avatar")
    except Exception as e:
        print(f"avatar download failed: {e}", file=sys.stderr)
    deco_asset = deco.get("asset")
    if deco_asset:
        try:
            rasterize(
                f"https://cdn.discordapp.com/avatar-decoration-presets/{deco_asset}.png",
                128, os.path.join(OUT_DIR, "decoration.png"),
            )
            print("downloaded decoration")
        except Exception as e:
            print(f"decoration download failed: {e}", file=sys.stderr)

    out = {
        "configured": True,
        "user_id": user_id,
        "username": du.get("username") or "Discord",
        "display_name": du.get("display_name") or du.get("global_name")
        or du.get("username") or "Discord",
        "public_flags": du.get("public_flags", 0),
        "status": data.get("discord_status", "offline"),
        "active_on_mobile": data.get("active_on_discord_mobile", False),
        "active_on_desktop": data.get("active_on_discord_desktop", False),
        "spotify": data.get("spotify"),
        "listening_to_spotify": data.get("listening_to_spotify", False),
        "activities": data.get("activities", []),
        "avatar_b64": b64(os.path.join(OUT_DIR, "avatar.png")) if os.path.exists(
            os.path.join(OUT_DIR, "avatar.png")) else "",
        "decoration_b64": b64(os.path.join(OUT_DIR, "decoration.png")) if os.path.exists(
            os.path.join(OUT_DIR, "decoration.png")) else "",
    }

    json.dump(out, open(OUT_JSON, "w"), indent=2)
    print(f"wrote {OUT_JSON}: {out['display_name']} is {out['status']} "
          f"(avatar {len(out['avatar_b64'])//1024}KB, deco {len(out['decoration_b64'])//1024}KB)")


if __name__ == "__main__":
    main()

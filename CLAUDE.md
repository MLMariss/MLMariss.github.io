# mlmariss.github.io — working instructions

## What this repo is
- GitHub Pages **user site**: `main` is served live at `https://mlmariss.github.io/`. A push to
  `main` is a deploy.
- Its job is to give Google the site name **MLMariss** (via the `WebSite` JSON-LD in
  `index.html`) for everything under this address, including QTPD at `/SteamQTPD/`. Keep that
  block and its `"name"` unchanged unless the owner asks; changing it resets what Google learned.
- `robots.txt` here is the only one crawlers read for the whole `mlmariss.github.io` address.
- The two cards (YouTube and QTPD) are deliberately **equal**: same style, side by side, YouTube
  first. Do not promote one over the other.

## Git handover — MANDATORY (same rules as SteamQTPD)

**The owner's single control point is the MERGE.** Everything up to the push is Claude's job.

- **Never push to `main`.** Work on a feature branch; the owner merges the pull request.
- **Ask once, then push.** Finish the whole task, commit, then ask "task is done — push?".
  Never push mid-task. If the owner says "commit and push" up front, that is the approval.
- **Never merge a pull request.** That is the owner's step.
- **Never delete branches.**
- After pushing, check for an existing open PR for the branch; otherwise open one. End the
  turn with the clickable PR URL.

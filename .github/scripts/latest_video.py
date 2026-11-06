#!/usr/bin/env python3
"""Save the newest long MLMariss video as latest-video.jpg + latest-video.json.

Run by .github/workflows/latest-video.yml. The home page shows these two files in its
click-to-play panel, so the panel can show the newest video without loading anything from
YouTube before the visitor clicks: the thumbnail is a copy hosted on this site.

  1. Read the feed of the long-videos uploads playlist (UULF..., the same playlist the panel
     plays, newest first). If that fails or is empty, read the channel feed instead and skip
     Shorts.
  2. Take the newest entry. If its video id equals the one in latest-video.json, stop and
     leave both files untouched, so the workflow has nothing to commit.
  3. Download maxresdefault.jpg (hqdefault.jpg when that is missing or is YouTube's 120x90
     placeholder), crop it to 16:9, resize to 1280x720 and save it at JPEG quality 82.
  4. Write latest-video.json: {"id", "title", "published", "url"}.

When YouTube does not answer (its feed server answers 404 to every feed for hours at a time,
and the Shorts check or thumbnail can fail the same way), both files stay as they are. With
--grace, the run then ends with a warning and exit code 0, unless YouTube has not answered
for that many hours, in which case it fails. --state is the file that remembers when YouTube
last answered; the workflow keeps it between runs in the Actions cache.

Usage: python latest_video.py [--force] [--out DIR] [--state FILE] [--grace HOURS]
  --force  rewrite both files even when the video id has not changed (to pick up a title or
           thumbnail edited after upload)
  --out    folder to write into (default: the current folder, the repo root in the workflow)
  --state  file holding the time YouTube last answered (written when it answers)
  --grace  hours YouTube may stay silent before a run fails (default 0: fail at once)
"""

import argparse
import datetime
import http.client
import io
import json
import os
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from PIL import Image

CHANNEL_ID = "UCApjzYvBluJ-CB52BfOxhyQ"
PLAYLIST_ID = "UULFApjzYvBluJ-CB52BfOxhyQ"  # uploads playlist, long videos only (no Shorts, no lives)
PLAYLIST_FEED = "https://www.youtube.com/feeds/videos.xml?playlist_id=" + PLAYLIST_ID
CHANNEL_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id=" + CHANNEL_ID

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; mlmariss-latest-video/1.0)",
    # Answers YouTube's cookie-consent wall in advance, so the Shorts check below sees the
    # real answer (a 200 or a redirect to /watch) rather than a redirect to the consent page.
    "Cookie": "SOCS=CAI",
}
TIMEOUT = 30
SIZE = (1280, 720)
QUALITY = 82
JPG_NAME = "latest-video.jpg"
JSON_NAME = "latest-video.json"


class Unavailable(Exception):
    """YouTube did not give an answer we can use (HTTP error, network error, not a feed)."""


def log(msg):
    print(msg, flush=True)


def set_output(name, value):
    """Pass a step output to the workflow (no-op outside GitHub Actions)."""
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write("%s=%s\n" % (name, value))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # urllib then raises HTTPError carrying the 3xx status


_follow = urllib.request.build_opener()
_no_redirect = urllib.request.build_opener(_NoRedirect)


def get(url, follow_redirects=True):
    """GET a URL; return (status, body). HTTP errors come back as their status; network
    errors raise Unavailable."""
    opener = _follow if follow_redirects else _no_redirect
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except (OSError, http.client.HTTPException) as e:  # DNS, refused, reset, timeout
        raise Unavailable("network error: %s" % e) from e


def is_short(video_id):
    """A video is a Short when /shorts/ID answers 200 itself. Long videos redirect to /watch."""
    status, _ = get("https://www.youtube.com/shorts/" + video_id, follow_redirects=False)
    if status == 200:
        return True
    if 300 <= status < 400:
        return False
    # Anything else (404, 429, 5xx) is not an answer. Stop rather than guess: a Short in
    # the panel would show a video the player does not play first.
    raise Unavailable("Shorts check for %s answered HTTP %s" % (video_id, status))


def read_feed(url):
    """Return the feed's entries as dicts, newest first. Raises Unavailable when unusable."""
    status, body = get(url)
    if status != 200:
        raise Unavailable("HTTP %s" % status)
    try:
        root = ET.fromstring(body)
    except ET.ParseError as e:
        raise Unavailable("not a feed (%s)" % e) from e
    entries = []
    for e in root.findall("atom:entry", NS):
        vid = (e.findtext("yt:videoId", "", NS) or "").strip()
        title = (e.findtext("atom:title", "", NS) or "").strip()
        published = (e.findtext("atom:published", "", NS) or "").strip()
        if vid and title:
            entries.append({"id": vid, "title": title, "published": published})
    # The feeds list newest first; sort anyway so the answer does not depend on that.
    # ISO 8601 timestamps in one time zone sort correctly as text.
    entries.sort(key=lambda x: x["published"], reverse=True)
    return entries


def newest_video():
    try:
        entries = read_feed(PLAYLIST_FEED)
        if entries:
            log("Playlist feed: %d entries" % len(entries))
            return entries[0]
        playlist_problem = "empty"
        log("Playlist feed is empty; falling back to the channel feed")
    except Unavailable as exc:
        playlist_problem = str(exc)
        log("Playlist feed failed (%s); falling back to the channel feed" % exc)

    try:
        entries = read_feed(CHANNEL_FEED)
    except Unavailable as exc:
        raise Unavailable("playlist feed: %s; channel feed: %s" % (playlist_problem, exc)) from exc
    log("Channel feed: %d entries" % len(entries))
    for entry in entries:
        if is_short(entry["id"]):
            log("  skip Short %s" % entry["id"])
            continue
        return entry
    raise Unavailable("playlist feed: %s; channel feed: no long video among its %d entries"
                      % (playlist_problem, len(entries)))


def download_thumbnail(video_id):
    """Return the best thumbnail as a PIL image: maxresdefault, else hqdefault."""
    for name in ("maxresdefault", "hqdefault"):
        url = "https://i.ytimg.com/vi/%s/%s.jpg" % (video_id, name)
        status, body = get(url)
        if status != 200:
            log("%s: HTTP %s" % (name, status))
            continue
        img = Image.open(io.BytesIO(body))
        img.load()
        if img.size == (120, 90):  # YouTube's "no thumbnail" placeholder
            log("%s: 120x90 placeholder" % name)
            continue
        log("%s: %dx%d" % (name, img.width, img.height))
        return img
    raise Unavailable("no thumbnail for %s yet" % video_id)


def to_16x9(img):
    """Center-crop to 16:9 (hqdefault is 4:3 with black bars) and resize to SIZE."""
    img = img.convert("RGB")
    w, h = img.size
    target = SIZE[0] / SIZE[1]
    if w / h > target:  # too wide: trim the sides
        cw = round(h * target)
        left = (w - cw) // 2
        img = img.crop((left, 0, left + cw, h))
    elif w / h < target:  # too tall: trim top and bottom
        ch = round(w / target)
        top = (h - ch) // 2
        img = img.crop((0, top, w, top + ch))
    return img.resize(SIZE, Image.LANCZOS)


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)


def stamp(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def read_last_answer(path):
    """When YouTube last answered, from the state file; None when unknown."""
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return datetime.datetime.fromisoformat(f.read().strip())
    except (OSError, ValueError):
        return None


def write_last_answer(path, t):
    if not path:
        return
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(stamp(t) + "\n")
    set_output("state_changed", "true")


def youtube_unavailable(problem, state_path, grace_hours):
    """Report an outage. Returns the exit code: 0 inside the grace period, else 1."""
    now = now_utc()
    last = read_last_answer(state_path)
    if last is None:
        # No record (first run, or the cache expired): start counting from this run, so a
        # long outage still fails the run once the grace period has passed.
        write_last_answer(state_path, now)
        since = "no earlier answer on record, so counting from now"
        hours = 0.0
    else:
        hours = (now - last).total_seconds() / 3600
        since = "it last answered %s (%.0f h ago)" % (stamp(last), hours)

    if grace_hours > 0 and hours < grace_hours:
        # A ::warning:: line shows on the run's page but sends no email.
        print("::warning title=YouTube unavailable::%s. Both files are unchanged and the next "
              "run tries again. %s; runs start failing once that reaches %g h."
              % (problem, since[0].upper() + since[1:], grace_hours), flush=True)
        return 0
    if grace_hours > 0:
        print("::error title=YouTube unavailable for %.0f hours::%s. Both files are unchanged. "
              "%s. If this goes on, check the feed URLs in .github/scripts/latest_video.py."
              % (hours, problem, since[0].upper() + since[1:]), flush=True)
    else:
        print("::error title=YouTube unavailable::%s. Both files are unchanged; this is "
              "usually a YouTube outage, and the next run tries again." % problem, flush=True)
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--out", default=".")
    ap.add_argument("--state", default=None)
    ap.add_argument("--grace", type=float, default=0.0)
    args = ap.parse_args()

    jpg_path = os.path.join(args.out, JPG_NAME)
    json_path = os.path.join(args.out, JSON_NAME)

    old_id = None
    try:
        with open(json_path, encoding="utf-8") as f:
            old_id = json.load(f).get("id")
    except (OSError, ValueError):
        pass

    try:
        video = newest_video()
        log("Newest: %s  %s  %r" % (video["id"], video["published"], video["title"]))
        unchanged = old_id == video["id"] and os.path.exists(jpg_path) and not args.force
        thumb = None if unchanged else to_16x9(download_thumbnail(video["id"]))
    except Unavailable as exc:
        return youtube_unavailable(str(exc), args.state, args.grace)
    write_last_answer(args.state, now_utc())

    if unchanged:
        log("Same video as latest-video.json; nothing to do")
        return 0

    thumb.save(jpg_path, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    log("Wrote %s (%d bytes)" % (jpg_path, os.path.getsize(jpg_path)))

    data = {
        "id": video["id"],
        "title": video["title"],
        "published": video["published"],
        "url": "https://www.youtube.com/watch?v=" + video["id"],
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    log("Wrote %s" % json_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

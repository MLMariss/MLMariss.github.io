#!/usr/bin/env python3
"""Save the newest long MLMariss video as latest-video.jpg + latest-video.json.

Run by .github/workflows/latest-video.yml. The home page shows these two files in its
click-to-play panel, so the panel can show the newest video without loading anything from
YouTube before the visitor clicks: the thumbnail is a copy hosted on this site.

  1. Read the feed of the long-videos uploads playlist (UULF..., the same playlist the panel
     plays, newest first). If that fails or is empty, read the channel feed instead and skip
     Shorts. YouTube's feed server sometimes answers 404 for every feed for a while, so each
     feed gets TRIES tries before it counts as failed. When both fail, the run fails with an
     error annotation and both files stay as they are.
  2. Take the newest entry. If its video id equals the one in latest-video.json, stop and
     leave both files untouched, so the workflow has nothing to commit.
  3. Download maxresdefault.jpg (hqdefault.jpg when that is missing or is YouTube's 120x90
     placeholder), crop it to 16:9, resize to 1280x720 and save it at JPEG quality 82.
  4. Write latest-video.json: {"id", "title", "published", "url"}.

Usage: python latest_video.py [--force] [--out DIR]
  --force  rewrite both files even when the video id has not changed (to pick up a title or
           thumbnail edited after upload)
  --out    folder to write into (default: the current folder, the repo root in the workflow)
"""

import argparse
import io
import json
import os
import sys
import time
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
TRIES = 3                # per feed
RETRY_WAITS = (20, 40)   # seconds to wait before the 2nd and 3rd try
SIZE = (1280, 720)
QUALITY = 82
JPG_NAME = "latest-video.jpg"
JSON_NAME = "latest-video.json"


def log(msg):
    print(msg, flush=True)


def get(url):
    """GET a URL; return (status, body). Raises on network errors, returns HTTP errors."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # urllib then raises HTTPError carrying the 3xx status


_no_redirect = urllib.request.build_opener(_NoRedirect)


def is_short(video_id):
    """A video is a Short when /shorts/ID answers 200 itself. Long videos redirect to /watch."""
    req = urllib.request.Request("https://www.youtube.com/shorts/" + video_id, headers=HEADERS)
    try:
        with _no_redirect.open(req, timeout=TIMEOUT) as r:
            return r.status == 200
    except urllib.error.HTTPError as e:
        if 300 <= e.code < 400:
            return False
        # Anything else (404, 429, 5xx) is not an answer. Stop rather than guess: a Short in
        # the panel would show a video the player does not play first.
        raise RuntimeError("Shorts check for %s answered HTTP %s" % (video_id, e.code))


class FeedsUnavailable(RuntimeError):
    """Neither YouTube feed could be read, even after retrying."""


def read_feed(url, label):
    """read_feed_once, tried up to TRIES times. Raises the last error when every try fails."""
    for attempt in range(1, TRIES + 1):
        try:
            return read_feed_once(url)
        except Exception as exc:  # noqa: BLE001 (HTTP errors, network errors, bad XML)
            if attempt == TRIES:
                raise
            wait = RETRY_WAITS[attempt - 1]
            log("%s feed failed (%s), try %d of %d; retrying in %ds"
                % (label, exc, attempt, TRIES, wait))
            time.sleep(wait)


def read_feed_once(url):
    """Return the feed's entries as dicts, newest first. Raises when the feed is unusable."""
    status, body = get(url)
    if status != 200:
        raise RuntimeError("HTTP %s" % status)
    root = ET.fromstring(body)
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
        entries = read_feed(PLAYLIST_FEED, "Playlist")
        if entries:
            log("Playlist feed: %d entries" % len(entries))
            return entries[0]
        playlist_problem = "empty"
        log("Playlist feed is empty; falling back to the channel feed")
    except Exception as exc:  # noqa: BLE001 (any failure means: use the fallback)
        playlist_problem = str(exc)
        log("Playlist feed failed (%s); falling back to the channel feed" % exc)

    try:
        entries = read_feed(CHANNEL_FEED, "Channel")
    except Exception as exc:  # noqa: BLE001
        raise FeedsUnavailable(
            "Both YouTube feeds failed after %d tries each (playlist: %s; channel: %s)"
            % (TRIES, playlist_problem, exc)) from exc
    log("Channel feed: %d entries" % len(entries))
    for entry in entries:
        if is_short(entry["id"]):
            log("  skip Short %s" % entry["id"])
            continue
        return entry
    raise RuntimeError("no long video in the channel feed")


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
    raise RuntimeError("no thumbnail for %s" % video_id)


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--out", default=".")
    args = ap.parse_args()

    jpg_path = os.path.join(args.out, JPG_NAME)
    json_path = os.path.join(args.out, JSON_NAME)

    try:
        video = newest_video()
    except FeedsUnavailable as exc:
        # An ::error:: line becomes the run's annotation, so the failure email says why.
        print("::error title=YouTube feeds unavailable::%s. Both files were left unchanged; "
              "this is usually a YouTube outage, and the next scheduled run tries again." % exc,
              flush=True)
        return 1
    log("Newest: %s  %s  %r" % (video["id"], video["published"], video["title"]))

    old_id = None
    try:
        with open(json_path, encoding="utf-8") as f:
            old_id = json.load(f).get("id")
    except (OSError, ValueError):
        pass
    if old_id == video["id"] and os.path.exists(jpg_path) and not args.force:
        log("Same video as latest-video.json; nothing to do")
        return 0

    thumb = to_16x9(download_thumbnail(video["id"]))
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

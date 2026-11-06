# mlmariss.github.io

The home page of `https://mlmariss.github.io/`: one page that ties the MLMariss YouTube channel
and the free tools together under one name, **MLMariss**.

## What it is for

1. **Give Google the site name "MLMariss"** for every page under this address. Google reads a
   site name only from the home page of a host (it cannot be set from a sub-folder such as
   `/SteamQTPD/`). Without this page, results for QTPD and the Dawnwalker planner showed a generic
   "GitHub Pages" label. The `WebSite` block in `index.html` carries the name; keep its `"name"`
   stable, because changing it resets what Google has learned.
2. **Say who MLMariss is, once.** The `Person` block links this site, the YouTube channel and the
   GitHub account (`sameAs`) so search engines and AI answers treat them as one creator.
3. **Be the front door.** Anyone who trims a tool's URL back to `mlmariss.github.io` lands here
   instead of a 404, and gets the channel and every tool in one place.
4. **Hold the crawler rules for the whole address.** Crawlers read `robots.txt` only at the host
   root, so this repo's `robots.txt` is the only one that counts for every project below.

## How the pieces fit

Each project is its own GitHub repository, published by GitHub Pages as a sub-folder of this
address. This repo only owns the root.

| Address | Repository | What it is |
|---|---|---|
| `https://mlmariss.github.io/` | `MLMariss/MLMariss.github.io` (this repo) | Home page, site name, `robots.txt` |
| `https://www.youtube.com/@MLMariss` | (YouTube) | The main profile: PC gaming guides and Steam deal breakdowns |
| `https://mlmariss.github.io/SteamQTPD/` | `MLMariss/SteamQTPD` | QTPD: ranks Steam games by well-reviewed hours per dollar |
| `https://mlmariss.github.io/DawnWalker/` | `MLMariss/DawnWalker` | The Blood of Dawnwalker skill tree planner |

```
                 www.youtube.com/@MLMariss   (main profile)
                              ▲
                              │ card + Person sameAs
                              │
   mlmariss.github.io/  ──────┤  index.html: WebSite "MLMariss" + Person
   robots.txt, sitemap.xml    │
                              ├──► /SteamQTPD/   card + "About the tools" link
                              └──► /DawnWalker/  card + "About the tools" link
```

### Page layout (owner's call)

- **Top:** the YouTube channel as one full-width card. It is the main profile: avatar, links to
  the channel, and a click-to-play panel for the uploads playlist (`UULF…`, long videos, newest
  first). The panel shows the newest long video's thumbnail and title, the same video the
  player starts with. Both come from this site's own copies (`latest-video.jpg`,
  `latest-video.json`), which a scheduled workflow refreshes, so nothing from YouTube
  (`youtube.com`, `ytimg.com`, `googlevideo.com`) loads until someone clicks. Then a
  `youtube-nocookie.com` player replaces the panel. Without JavaScript the panel still shows the
  thumbnail and is a plain link to the playlist; the title needs JavaScript, and without it (or
  if `latest-video.json` cannot be read) the label reads "Play the latest videos".
- **"Free tools":** equal cards side by side (stacked on phones), QTPD first, then the
  Dawnwalker planner.
- **About:** one collapsed entry per item (the channel, then each tool), built with
  `<details>`. The heading and a one-line summary stay visible; the full text opens on a click.
  The folded text is real text in the HTML, so search engines and AI answers still read and
  quote it, while the page stays short for visitors. It states what each thing does in specific
  terms. The QTPD entry is a short version of QTPD's own text and links to its "Ways to use
  QTPD" section (`/SteamQTPD/#ways-to-use`): the full keyword-bearing copy lives on the QTPD page,
  so this page points to it rather than competing with it for the same searches.

### Search files in this repo

- `index.html`: title, description, canonical, Open Graph tags, the Google Search Console
  verification tag (removing it un-verifies the property), and the `WebSite` + `Person`
  structured data.
- `robots.txt`: allows all crawlers and lists one `Sitemap:` line per project.
- `sitemap.xml`: lists the home page only, with `<lastmod>` set to the date of the last real
  content change (update it when the page's text changes, not on every edit). Each project keeps
  its own sitemap in its own repo.
- `404.html`: the "page not found" page for mistyped addresses under `mlmariss.github.io`.
  GitHub Pages sends it with a real 404 status. It links home, the channel and every tool, with
  absolute links because it can be served at any path.
- `favicon.svg`: the MLMariss "M" icon. Google shows one icon per site, taken from this home
  page, so this is the icon next to every result under `mlmariss.github.io`, tools included.
- `apple-touch-icon.png`: the same "M" as a 180×180 PNG, for iPhones and apps that ignore SVG icons.
- `avatar.jpg`: the channel picture (256×256), shown in the YouTube card and used as the
  `Person` image in the structured data.
- `og-image.png`: the 1200×630 preview image shown when the home page is shared.
- `.nojekyll`: serves the files as-is, without GitHub's Jekyll build.

### Newest-video files (written by a workflow, not by hand)

- `latest-video.jpg`: the newest long video's thumbnail, copied from YouTube and resized to
  1280×720 (JPEG quality 82). The background of the click-to-play panel.
- `latest-video.json`: that video's `id`, `title`, `published` date and `url`. The page reads the
  title from it for the panel's label.
- `.github/workflows/latest-video.yml`: refreshes both files every 3 hours, or on demand from the
  Actions tab ("Run workflow"; tick *force* to pick up a title or thumbnail edited after upload).
  It commits only when the newest video's id has changed. It also runs when its own files change
  on a `claude/` branch, so a pull request that changes it carries real output.
- `.github/scripts/latest_video.py`: what the workflow runs. It reads the feed of the long-videos
  playlist (`UULF…`) and falls back to the channel feed (skipping Shorts) when that fails or is
  empty. It takes `maxresdefault.jpg`, or `hqdefault.jpg` (cropped to 16:9) when the larger
  one is missing.
- **When YouTube does not answer:** YouTube's feed server sometimes answers 404 to every feed
  for hours. Then both files stay as they are. A scheduled run ends green with a "YouTube
  unavailable" warning on its page, and GitHub sends no email for it. The job fails (and emails)
  only after YouTube has not answered for 48 hours, which means something is really broken,
  such as a retired feed URL. The time YouTube last answered is a small text file kept between
  runs in the Actions cache, never committed. Manual and branch runs fail on an outage straight
  away, since someone is watching them.

## Adding a new project

1. Publish the project from its own repo with GitHub Pages (it appears at
   `https://mlmariss.github.io/<RepoName>/`).
2. Add a card to the "Free tools" section of `index.html` and a collapsed entry to the
   "About" section (heading, one-line summary, a short paragraph), and a link in `404.html`.
3. Add its sitemap to `robots.txt`: `Sitemap: https://mlmariss.github.io/<RepoName>/sitemap.xml`.
4. Mention it in the `Person` description and the page's meta description if it changes what
   MLMariss is known for.

## Publishing

`main` is live. Changes go through a branch and a pull request; the owner merges.

**One exception (owner, 2026-11-03):** the `latest-video.yml` workflow commits
`latest-video.jpg` and `latest-video.json` straight to `main` as `github-actions[bot]` when a new
long video appears. It stages those two files by name and nothing else. Each such commit
redeploys the site.

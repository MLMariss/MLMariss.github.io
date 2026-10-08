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

- **Top:** the YouTube channel as one full-width card. It is the main profile.
- **"Free tools":** equal cards side by side (stacked on phones), QTPD first, then the
  Dawnwalker planner.
- **About:** plain text describing the channel and each tool, with links. This is the text
  search engines and AI answers can quote, so it states what each thing does in specific terms.

### Search files in this repo

- `index.html`: title, description, canonical, Open Graph tags, the Google Search Console
  verification tag (removing it un-verifies the property), and the `WebSite` + `Person`
  structured data.
- `robots.txt`: allows all crawlers and lists one `Sitemap:` line per project.
- `sitemap.xml`: lists the home page only. Each project keeps its own sitemap in its own repo.
- `favicon.svg`: the MLMariss "M" icon. Google shows one icon per site, taken from this home
  page, so this is the icon next to every result under `mlmariss.github.io`, tools included.
- `og-image.png`: the 1200×630 preview image shown when the home page is shared.
- `.nojekyll`: serves the files as-is, without GitHub's Jekyll build.

## Adding a new project

1. Publish the project from its own repo with GitHub Pages (it appears at
   `https://mlmariss.github.io/<RepoName>/`).
2. Add a card to the "Free tools" section of `index.html` and a short paragraph under
   "About the tools".
3. Add its sitemap to `robots.txt`: `Sitemap: https://mlmariss.github.io/<RepoName>/sitemap.xml`.
4. Mention it in the `Person` description and the page's meta description if it changes what
   MLMariss is known for.

## Publishing

`main` is live. Changes go through a branch and a pull request; the owner merges.

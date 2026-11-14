# Global working preferences
Apply to every project unless the project's CLAUDE.md says otherwise.

# Branches
* Never edit, commit or push on `main` or `master`. I merge into `main` myself on GitHub.
* For each new task, create a fresh branch from the latest origin/main, named after the change (for example fix-date-compare). Keep working on that branch until its PR is merged.
* Don't delete branches.
* If you find yourself on `main` or `master`, stop and tell me.
* In Claude Code on the web, the session's own branch is the task branch.

# How to work
* Read the relevant files before answering or changing anything. Don't guess about code you haven't opened.
* Write a general solution, not one that only passes the tests. Don't hard-code values to make a test pass. If a test looks wrong, tell me instead of working around it.
* Keep changes to what the task needs: no refactoring unrelated code, extra features, comments on untouched code, or error handling for cases that can't happen. Small diffs are easier for me to review.
* When you say something works, name the command you ran and what it returned.

# When stuck or unsure
* If the same approach fails twice, stop. Tell me what you tried, what the errors said, and your best guess at the cause, then ask how to continue.
* When a choice would change what you build and the code doesn't answer it, use the AskUserQuestion tool with 2 to 4 options, your recommendation first.
* Ask before anything hard to undo: deleting files, force pushing, rewriting git history, changing shared settings, or skipping checks like --no-verify.

# Finishing a task
* When a coding task is done, commit, then end with AskUserQuestion offering the next steps that fit, your recommendation first. Usual options:
  * Push the task branch and open or update the PR into `main`, then give me the PR link
  * Review the diff with a subagent in a fresh context first (fix only issues that affect correctness or the requirements)
  * Keep the commit local for now
  * Stop here
* Push once per finished task, only after I pick it. Never push mid-task.
* Never merge a PR. Merging is my step.
* Leave out options that don't apply. Don't ask after plain questions or explanations.
* If AskUserQuestion isn't available, give the same options as a short numbered list so I can answer with a number.

# Context
* When I switch to an unrelated topic, suggest /clear.
* When compacting, keep the list of modified files and the test commands.

# This project
* GitHub Pages **user site**: `main` (root folder) is served live at `https://mlmariss.github.io/`. A merge into `main` is a deploy.
* Its job is to give Google the site name **MLMariss** (via the `WebSite` JSON-LD in `index.html`) for everything under this address, including QTPD at `/SteamQTPD/`. Keep that block and its `"name"` unchanged unless the owner asks; changing it resets what Google learned.
* `robots.txt` here is the only one crawlers read for the whole `mlmariss.github.io` address.
* Page hierarchy (owner's call): the **YouTube channel is the main profile** and sits on top as the full-width card. Below it, "Free tools": equal cards side by side, QTPD first, then the Dawnwalker skill tree planner. A new project gets a card in that section, and its sitemap a `Sitemap:` line in `robots.txt`.
* **A workflow commits to `main` (owner's exception, 2026-11-03):** `.github/workflows/latest-video.yml` runs every 3 hours and commits `latest-video.jpg` and `latest-video.json` straight to `main` as `github-actions[bot]`, only when the newest video's id, title or thumbnail has changed (title and thumbnail added by the owner, 2026-11-06). It stages those two files by name. Do not widen it to other files, and do not add another workflow that writes to `main`, without asking. The exception covers that bot only, never Claude.
* Because of that bot, `main` moves on its own: fetch before branching.

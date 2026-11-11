# ReggaeLive — handoff notes

Background for a new Claude chat picking up this project. Read this, then `tools/update/common.md`,
`tools/update/east.md` and `tools/ADDING_A_CITY.md`.

## What the site is
- A sister site of LaughsLive (repo Laughslive/Laughslive): a "Bandsintown for Caribbean music".
  It lists reggae, dancehall, soca and calypso shows within 50 miles of the same 34 U.S. cities.
  Venue-first and privacy-first.
- **Repo:** `livereggaemusic`, branch `main`, served by GitHub Pages.
- **Name:** "ReggaeLive" is a placeholder. The name, domain and emails live in `data/site.json`. To rename, change:
  - the logo text `Reggae<span class="onair">Live</span>` in index.html and in `tools/build_pages.py`;
  - `"name"` in `data/site.json`;
  - `manifest.webmanifest`;
  - the "ReggaeLive" strings in `install.js` and `sw.js`.
- **`index.html` is the source of truth** for all show data.

## Owner's standing rules (same as LaughsLive)
- **Privacy first.**
  - No cookies, accounts, GPS or ad trackers.
  - Never put the owner's personal email anywhere public or send it to outside services.
- **Venue / promoter first.**
  - The official seller is the link fans get.
  - Aggregators are backup only (list in `tools/update/common.md`).
- **Accuracy:** never guess times, prices, names or URLs. Skip a show with no stated start time.
- **Genre scope** (owner's choice: "wider Caribbean", plus African music added Nov 10, 2026): reggae (incl. reggae-rock
  and Jamaican-style ska), dancehall, soca, calypso, and afrobeats/amapiano/highlife/afro-pop (type `AF`).
  Not reggaeton/Latin, dubstep or ska-punk/2-tone.
- **Secrets** go in GitHub Actions secrets, never in code. The repo may be public.
- **Before acting:** explain GitHub steps in plain words, and ask before anything irreversible.
- **Commits:** author `-c user.name="ReggaeLive" -c user.email="reggaelive@users.noreply.github.com"`,
  messages end with a `Co-Authored-By:` line.

## Differences from LaughsLive's code
- **Show types:** `RG` Reggae, `DH` Dancehall, `SC` Soca & calypso, `AF` Afrobeats & African, defined in the app script.
  - Flag `"fest"` = festival or carnival.
  - The artist search uses `?artist=` (it's `?comic=` on LaughsLive).
- **`data/site.json`:** name, domain, email addresses and the IndexNow key, all in one place.
  - Blank email addresses are left off the pages: no "Submit a show" link and no contact section until they're set.
  - The IndexNow key file `<key>.txt` sits at the repo root.
- **`tools/fetch_ticketmaster.py`:**
  - Searches each city by Ticketmaster classification name (Reggae, Dancehall, Soca, Calypso, Caribbean)
    and by keyword, within the Music segment, 90 days ahead.
  - Keeps an event only if Ticketmaster files it under one of those genres, or (for keyword hits) its own name contains a genre word.
  - Each event records `why` it was kept, and the run prints a summary for tuning.
  - **Artist watch list:** `data/watch_artists.json` (about 105 names, each with a type). Every artist is also searched
    by name U.S.-wide, so their Ticketmaster shows come in even when Ticketmaster files them under Pop or Hip-Hop
    (Tyla, for example). Names must match a listed performer or appear as whole words in the event name.
  - In total it's about 700 API calls a day, well under Ticketmaster's 5,000/day.
- **`tools/merge_ticketmaster.py`:**
  - Picks the show type from the genres and the event name.
  - Flags festivals.
  - Its `EXCLUDE` pattern drops reggaeton and non-show items (parking, upgrades…).
  - Its block-finding pattern also handles empty generated blocks; LaughsLive's version can't, but it never has empty blocks.
- **Colors:** red/gold/green on dark green. Display font: Rubik Mono One. New icons in `icons/`.
- **CNAME:** none yet. Add one with the domain when it's bought.

## Still to do (owner)
1. **Turn on GitHub Pages:** Settings → Pages → Deploy from branch `main`, folder `/ (root)`.
   - Until a custom domain is set, the site lives at `<owner>.github.io/livereggaemusic/`.
   - At that address, links that start with `/` (icons, city pages, the app files) don't work. So judge the
     site on the real domain, or preview locally.
2. **Ticketmaster key:** Settings → Secrets and variables → Actions → New repository secret `TM_API_KEY`.
   The same key as LaughsLive is fine. Then run "Ticketmaster reggae feed" from the Actions tab once.
3. **Domain:** livereggaemusic.com (CNAME file and `data/site.json` are set). Point its DNS at GitHub Pages.
4. **Email:** set up the addresses and fill them into `data/site.json`.
   - The Proton plan allows one custom domain, already used by laughslive.com. Either upgrade the plan or use another provider.
5. **Search engines and analytics:**
   - Google Search Console: put its verification tag in `tools/head_extra.html`.
   - Cloudflare Web Analytics: put its beacon in `tools/head_extra.html`. The Privacy page already describes it.
   - Bing Webmaster.
6. **Scheduled Claude updates:** create twice-weekly tasks (East and West) that follow `tools/update/east.md` and `west.md`.
   - Offset their times from the LaughsLive tasks.
   - The web reader only opens URLs found by search or listed in the task prompt, so put the confirmed venue,
     promoter and artist URLs in the prompts too.

## State at handoff (Nov 10, 2026)
- 14 hand-checked shows: UB40, The Slackers, Shaggy, Bumpin' Uglies, Holidaze (Boca Raton) and Steel Pulse NYE (Berkeley).
- Several of them link to aggregators because no official page could be opened. The ticket button then goes to the
  venue's site or a search, never the aggregator.
- Winter is the off-season. Expect most early listings to come from the Ticketmaster feed.
- Dancehall/soca parties need live checks of promoters' Eventbrite/Dice pages. Search results for them are often months old.

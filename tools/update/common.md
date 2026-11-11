# Live Reggae Music update — shared rules (read with east.md or west.md)

Live Reggae Music (livereggaemusic.com; name and domain in data/site.json) lists reggae, dancehall, soca, calypso and African music (afrobeats, amapiano, highlife, afro-pop) shows within 50 miles of 34 U.S. city centers. It is served by GitHub Pages from this repository (branch main). index.html holds all show data and is THE source of truth — work directly in it. Each scheduled run follows east.md or west.md, which add the region's cities, venues and promoters to these rules.

## What counts
- **RG Reggae:** roots, lovers rock, dub, reggae-rock (Rebelution, SOJA, Stick Figure, Slightly Stoopid and similar), and Jamaican-style ska/rocksteady bands (e.g. The Slackers).
- **DH Dancehall:** dancehall artists and dancehall-billed concerts.
- **SC Soca & calypso:** soca, calypso, steelpan and carnival fetes.
- **AF Afrobeats & African** (owner added Nov 10, 2026): afrobeats, afro-pop, afro-fusion, amapiano, highlife, bongo flava, soukous/ndombolo and other African artists' concerts, plus afrobeats-billed nights with a named headliner or DJ. Afro Nation and similar festivals get the "fest" flag.
- **Festivals:** add the flag "fest" for festivals, carnivals and J'ouvert events.
- **Skip:**
  - reggaeton and other Latin acts, even when a site files them under reggae (e.g. Rawayana, Kapo);
  - dubstep and bass-music DJs (Svdden Death, Bear Grillz, Liquid Stranger…);
  - ska-punk and 2-tone acts (The English Beat, The Pietasters, Reel Big Fish);
  - brunches and day parties with no named headliner or DJ;
  - open mics, karaoke and dance classes;
  - cruises and events outside the 50-mile areas.
- **Recurring parties:** DJ nights and weekly parties count only when they have a named headliner or sound system and a stated start time. Keep them to the ones a fan would plan around, at most one row per party per week.

## Sourcing policy (owner's standing rule)
- **Send fans to the official seller.** The primary source and link are, in order:
  1. the show's own page on the venue's or promoter's site;
  2. its official primary ticket page — Ticketmaster, AXS, Eventbrite, Dice, Tixr, Etix, SeeTickets, Ticketweb, Prekindle, Venue Pilot, Caribtix, Showclix, the venue's own box office;
  3. the artist's official tour page.
- **Resale and listing sites are the fallback** (owner's rule, updated Nov 10, 2026: "go to resale if the official seller, venue or artist aren't available"): concerts50, concertfix, new-york.events, americanarenas, eventworld, stereoboard, catchmovement, beatstorapon, discotech, jambase, bandsintown, songkick, seatgeek, vividseats, stubhub, tickpick, gametime and similar.
  - Use them to discover shows, or as the source only when no official page can be found.
  - Then still look for the official page before falling back to the aggregator link.
- **When there's no official link:** use the resale or listing page as the row's url. The ticket button then goes to the venue's own site (SITES) if there is one, and otherwise to that resale page, labeled "Resale tickets". Prefer real marketplaces (SeatGeek, StubHub, Vivid Seats, TickPick, Gametime) over pure listing sites. LISTING_SITE in index.html must match every resale/listing domain, so official links are always tried first.
- **Watch for look-alikes.** Resale sites built to look like the artist, such as <artist>tour2026.com or *.pages.dev, are never sources.
- **Accuracy.**
  - Never guess times, prices, names or URLs.
  - Skip a show unless a source you retrieved states its date, start time and venue.
  - When sources disagree on the time, use the official one. If there's no official source, skip the show and let the Ticketmaster feed carry it.
  - Use show time, not doors. Many dancehall bills list "doors 9 PM" with the headliner after midnight: list the advertised start time, never a guessed set time.
  - A show after midnight belongs to the previous night's date only if the source lists it that way.

## Ticketmaster feed
- A GitHub Action (.github/workflows/ticketmaster.yml) runs every morning. It fetches Ticketmaster's reggae / dancehall / soca / calypso listings for all 34 cities into data/ticketmaster.json, merges them into index.html with tools/merge_ticketmaster.py, rebuilds the city pages and publishes.
- Don't research Ticketmaster-sold arena and theater shows. Spend the time on what Ticketmaster misses: Eventbrite, Dice and Tixr events, promoter concerts, clubs, sound systems and carnival events.
- The feed also searches every artist in data/watch_artists.json by name. When the owner adds an artist to the watch list in east.md, add them there too (with type RG, DH, SC or AF).
- The feeds are filtered by Ticketmaster's and SeatGeek's own genre labels, so mislabeled shows slip in (radio holiday shows, ska-punk, Latin acts, generic club nights). Each run, scan the generated block for shows that don't count and add a specific pattern for each to data/feed_exclude.json (not to the code). Never add Ticketmaster's "Amapiano" label back: it sits on most EDM/club events.
- Also: the feed is filtered by Ticketmaster's own genre labels, so mislabeled shows can slip in. If you see one that doesn't count (above), add a pattern for it to EXCLUDE in tools/merge_ticketmaster.py.

## Fetching tips
- WebFetch only opens URLs that appeared in a WebSearch result, in an earlier fetched page, or in the task prompt.
  - Fetch a listing page first, then the event links that appear on it.
  - If a URL is refused, run a WebSearch that surfaces it (e.g. "<venue> <month> 2026 events") and fetch the result link.
  - Don't use curl or the shell: the shell can't reach outside websites, though git to GitHub works.
- **Search results for party listings are often months old.** Always open the event page itself and check that its date is in the future and in the right year.
- **Eventbrite:** organizer pages (eventbrite.com/o/<name>) list a promoter's upcoming events; each event page gives the date, start time and price.
- **Calendars that load by script:** look for a list view, the ticket seller's venue page, or the event's own page.
- Don't print or Read the whole of index.html. Edit it with small Python scripts that search for exact strings.

## The data (last <script> in index.html)
- **V: venues** `{n, area, b, lat, lng}`.
  - Coordinates decide which city lists a venue (within 50 miles of a center), so use the street address to get lat/lng right.
  - Add hand-checked venues above the `// <tm-venues>` block, under the city comment. Never edit that block.
- **SITES:** venue key → the venue's official site. Add one whenever you confirm a venue's site.
- **RAW rows:** `[date "YYYY-MM-DD", "HH:MM" (24h, several times joined with "|"), title, performers, venueKey, RG|DH|SC, url, price string or null, flags]`.
  - Flags: "fest", "out" (sold out), "18", "21". Add an age flag only when the source states it.
  - Hand rows go under the city's `// City` header, above `// <tm>`.
  - The rows between `// <tm>` and `// </tm>` are generated: never edit them. Hand rows always win; the merge skips Ticketmaster shows already listed by hand.
- **Prices:** leave the price null when it looks like resale. Prefer the seller's face value; a range like "$40–90" is fine.
- **Duplicates:** when an official page disagrees with an existing row (different act, date or time), the official page wins. Fix or remove the old row. Avoid duplicates.
- **Leave the code alone.** Change only the data blocks and the footer's "Listings gathered <date>" line.

## Publish (after each region, and at the end), from the repository root
1. `git pull --rebase` (the daily Ticketmaster Action also commits).
2. `python3 tools/merge_ticketmaster.py index.html data/ticketmaster.json data/seatgeek.json` rebuilds the Ticketmaster/SeatGeek block. Hand rows win, then Ticketmaster, then SeatGeek.
3. `python3 tools/check_script.py` must pass. If it fails, fix your last edit before going on.
4. `python3 tools/build_pages.py` must end with "wrote sitemap.xml and robots.txt". If it refuses because data/cities.json and the page disagree, fix the page. Never edit the city folders by hand.
5. `git add -A`, then commit with author `-c user.name="ReggaeLive" -c user.email="reggaelive@users.noreply.github.com"`. Use the message "Update listings <today's date> (<region>)", ending with a `Co-Authored-By:` line.
6. `git push`. If the push is rejected, pull --rebase and push again.

**Save as you go.** Publish after each region. If you're running low on room, stop researching and publish what you have.

## Finish
Send a short summary with SendUserMessage:
- per region: hand-checked shows removed and added;
- new venues, with suburban ones noted;
- new SITES entries;
- which regions were published, and if you stopped early, which are left;
- anything you couldn't verify;
- whether data/ticketmaster.json's "fetched" date is more than 3 days old, which means the GitHub Action may be failing.

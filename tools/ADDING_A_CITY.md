# Adding a city to Live Reggae Music

1. **data/cities.json** — add one entry: `code` (2–3 capital letters), `slug` (the web address, e.g. `san-diego`),
   `name`, `short` (used in page titles), `region` (one of `regions`; add a new region there if needed),
   `center` `[lat, lng]`, `states` (two-letter codes of every state within 50 miles) and `nearby`
   (a phrase of neighborhoods/suburbs for the page description).
   This alone updates the city pages, sitemap, footer links, the daily Ticketmaster download and the merge.

2. **The page itself** (index.html):
   - `Object.assign(CENTER,{…})` — the same center point.
   - `CITY_NAME` and `CITY_SLUG` — the name and the same slug.
   - a `<option value="CODE">` in the right `<optgroup>` of the City dropdown.
   - a `CODE_PLACES` table of neighborhoods/suburbs → [lat,lng], listed in `TABLES`; zip prefixes in `ZIP_PREFIX`;
     the state's abbreviation/name in the state-suffix pattern if it's a new state.
   - a `// City name` header in RAW for hand-checked shows.

3. **The twice-weekly Claude update's instructions** — add the city to the area list and its main venues.

4. Run `python3 tools/build_pages.py`. It refuses to build (and says what's missing) if step 1 and step 2 disagree.

Then run the "Ticketmaster reggae feed" action once from GitHub's Actions tab to pull the new city's shows right away.

## Scheduled updates
The twice-weekly updates are split into two runs that follow `tools/update/east.md`
(Northeast, Mid-Atlantic, South) and `tools/update/west.md` (Midwest, West).
When you add a city, add it to the area list, region list and venue list in the matching file.

## City intro text
Each city page ends with a short "Reggae in <city>" paragraph from `data/city_intros.json` (key = city code).
Add one for every new city, naming the main venues, festivals and series the site actually covers there.
`build_pages.py` prints a note for any city that is missing one.

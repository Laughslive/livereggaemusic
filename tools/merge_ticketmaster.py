#!/usr/bin/env python3
"""Merge data/ticketmaster.json (and data/seatgeek.json, if given) into the ReggaeLive page's show data.

    python3 tools/merge_ticketmaster.py <page.html> [data/ticketmaster.json [data/seatgeek.json ...]]

Files are merged in the order given, so Ticketmaster rows win over SeatGeek duplicates.

Edits <page.html> in place (the artifact file, or index.html). Ticketmaster rows
and any venues they need live in marked blocks:
    V:   // <tm-venues> ... // </tm-venues>
    RAW: // <tm> ... // </tm>
Both blocks are rebuilt from scratch on every run, so it is safe to re-run.
Shows already listed by hand (same venue and date, and the same start time or a
shared headliner name) are skipped, so hand-checked rows always win.
"""
import datetime, json, math, os, re, sys

GENERIC = set("""reggae dancehall soca calypso music concert band show shows live tour presents presented special night event
with the and festival fest york new friends late early main room hour evening vip sound system party
package experience club theatre theater tickets ticket an a of in at on for by from feat featuring plus guests""".split())

# Shows to leave out even when Ticketmaster files them under a Caribbean genre. Case-insensitive.
# Reggaeton is a Latin genre (not covered); parking passes, add-ons and upgrades aren't shows.
EXCLUDE = re.compile(r"reggaet[oó]n|\bparking\b|\bupgrade\b|add[- ]on\b|\bshuttle\b|\bcabana\b|\blocker\b|gift card", re.I)

def show_type(e):
    """RG reggae, DH dancehall, SC soca & calypso, AF afrobeats & African: from Ticketmaster's genres, then the event name."""
    if e.get("type") in ("RG", "DH", "SC", "AF"):   # set by the watch-list pass
        return e["type"]
    g = " ".join(e.get("genres") or []).lower() + " " + (e.get("why") or "").lower()
    n = (e.get("name") or "").lower()
    if re.search(r"afro|amapiano|highlife|african|bongo|soukous", n) or re.search(r"afro|amapiano|highlife|african|bongo|soukous", g):
        return "AF"
    if re.search(r"soca|calypso|carnival|j'?ouvert|\bfete\b|steel ?pan", n) or re.search(r"soca|calypso", g):
        return "SC"
    if "dancehall" in n or "dancehall" in g:
        return "DH"
    return "RG"

def miles(a, b):
    R = 3958.8
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))

def tokens(s):
    return {w for w in re.findall(r"[a-z0-9']+", (s or "").lower().replace("’", "'")) if len(w) > 2 and w not in GENERIC}

VENUE_GENERIC = set("""the theatre theater center centre hall club comedy at presented by music of for performing
arts live room main and in concert with house venue presents ga""".split())
# States each city area can reach within 50 miles (guards against bad venue coordinates in the feed)
import os as _os
_CITIES = json.load(open(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "data", "cities.json"),
                        encoding="utf-8"))["cities"]
CITY_STATES = {c["code"]: " ".join(c["states"]) for c in _CITIES}

def vtokens(s):
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if w not in VENUE_GENERIC}

def name_match(a, b, place=""):
    # Words of the town name don't count ("Brooklyn Bowl" is not "Brooklyn Paramount").
    drop = vtokens(place)
    ta, tb = vtokens(a) - drop, vtokens(b) - drop
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))

def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())

def strip_block(text, start, end):
    # (?:.*?\n)? so an empty block (no rows) is also found and replaced
    return re.sub(r"\n[ \t]*%s[^\n]*\n(?:.*?\n)?[ \t]*%s" % (re.escape(start), re.escape(end)), "", text, flags=re.S)

def main(page_path, *data_paths):
    data_paths = data_paths or ("data/ticketmaster.json",)
    page = open(page_path, encoding="utf-8").read()
    page = strip_block(page, "// <tm-venues>", "// </tm-venues>")
    page = strip_block(page, "// <tm>", "// </tm>")
    data = {"events": []}
    fetched = []
    for dp in data_paths:
        if not os.path.exists(dp):
            continue
        d = json.load(open(dp, encoding="utf-8"))
        data["events"] += d.get("events", [])
        if d.get("fetched"):
            fetched.append(("SeatGeek " if "seatgeek" in dp else "Ticketmaster ") + d["fetched"][:10])
    data["fetched"] = ", ".join(fetched)

    centers = {}
    for m in re.finditer(r"([A-Z]{2,3}):\[(-?[\d.]+),(-?[\d.]+)\]", page[page.index("const CENTER="):page.index("const CENTER=") + 3000]):
        centers[m.group(1)] = (float(m.group(2)), float(m.group(3)))
    for m in re.finditer(r"Object\.assign\(CENTER,\{([^}]*)\}", page):
        for k, a, b in re.findall(r"([A-Z]{2,3}):\[(-?[\d.]+),(-?[\d.]+)\]", m.group(1)):
            centers[k] = (float(a), float(b))

    v_start = page.index("const V={")
    v_end = page.index("\n};", v_start)
    venues = {}
    for m in re.finditer(r'\b(\w+):\{n:"((?:[^"\\]|\\.)*)"[^{}]*?lat:(-?[\d.]+),lng:(-?[\d.]+)\}', page[v_start:v_end]):
        venues[m.group(1)] = {"n": json.loads('"%s"' % m.group(2)), "ll": (float(m.group(3)), float(m.group(4)))}

    r_start = page.index("const RAW=[")
    r_end = page.index("\n];", r_start)
    S = r'"((?:[^"\\]|\\.)*)"'
    existing = {}  # (venue, date) -> list of (times set, name tokens)
    for m in re.finditer(r"\[%s,%s,%s,%s,\"(\w+)\"" % (S, S, S, S), page[r_start:r_end]):
        d, ts, title, who, vk = (json.loads('"%s"' % g) for g in m.groups()[:4]) , None, None, None, m.group(5)
        d, ts, title, who = d
        existing.setdefault((vk, d), []).append((set(ts.split("|")), tokens(title) | tokens(who)))

    today = datetime.date.today().isoformat()
    new_venues, rows, added = {}, [], set()
    skipped = {"dupe": 0, "status": 0, "far": 0, "nogeo": 0}
    for e in data["events"]:
        if (e.get("status") or "").lower() in ("cancelled", "canceled", "postponed"):
            skipped["status"] += 1; continue
        if e["date"] < today:
            continue
        if EXCLUDE.search(e.get("name") or "") or any(EXCLUDE.search(x or "") for x in e.get("attractions") or []):
            skipped["excluded"] = skipped.get("excluded", 0) + 1; continue
        if e.get("lat") is None or e.get("lng") is None:
            skipped["nogeo"] += 1; continue
        ll = (e["lat"], e["lng"])
        c = min(centers, key=lambda k: miles(centers[k], ll))   # nearest city center
        if miles(centers[c], ll) > 50 or (e.get("state") or "") not in CITY_STATES.get(c, "").split():
            skipped["far"] += 1; continue
        # find the venue: same name (ignoring words like "Theatre", "Comedy Club") within 5 miles
        key, best = None, (0.0, 9e9)
        for k, v in list(venues.items()) + list(new_venues.items()):
            dist = miles(v["ll"], ll)
            if dist > 5:
                continue
            score = name_match(v["n"], e["venue"], e.get("venueCity"))
            if score >= 0.5 and (score, -dist) > (best[0], -best[1]):
                key, best = k, (score, dist)
        if key is None:
            base = "tm_" + re.sub(r"[^a-z0-9]+", "_", (e["venue"] or "venue").lower()).strip("_")[:28]
            key = base; i = 2
            while key in venues or key in new_venues:
                key = f"{base}{i}"; i += 1
            new_venues[key] = {"n": e["venue"].strip(), "ll": ll, "area": e.get("venueCity") or "",
                               "b": e.get("state") or "", "c": c}
        names = tokens(e["name"]) | set().union(*[tokens(a) for a in e.get("attractions") or []] or [set()])
        dup = False
        for times, toks in existing.get((key, e["date"]), []):
            if e["time"] in times or (names and toks and names & toks):
                dup = True; break
        sig = (key, e["date"], e["time"])
        if dup or sig in added:
            skipped["dupe"] += 1; continue
        added.add(sig)
        existing.setdefault((key, e["date"]), []).append(({e["time"]}, names))
        who = ", ".join(a for a in (e.get("attractions") or []) if a and a.lower() not in e["name"].lower())[:120]
        if not who and e.get("attractions"):
            who = e["attractions"][0]
        pmin, pmax = e.get("priceMin"), e.get("priceMax")
        price = None
        if pmin and pmin > 0:
            price = f"${round(pmin)}" + (f"–{round(pmax)}" if pmax and round(pmax) > round(pmin) else "")
        typ = show_type(e)
        flags = ["fest"] if re.search(r"festival|\bfest\b|carnival", e["name"], re.I) else []
        if e.get("ageRestricted") and re.search(r"\b21\+|21 ?(and|&) ?over", e["name"], re.I): flags.append("21")
        rows.append((c, e["date"], e["time"],
                     f' [{json.dumps(e["date"])},{json.dumps(e["time"])},{json.dumps(e["name"], ensure_ascii=False)},'
                     f'{json.dumps(who, ensure_ascii=False)},"{key}",{typ},{json.dumps(e["url"])},{json.dumps(price, ensure_ascii=False)}{("," + json.dumps(flags)) if flags else ""}],'))

    vblock = "\n// <tm-venues>  (added automatically from the Ticketmaster feed; rebuilt each update)\n" + "".join(
        f' {k}:{{n:{json.dumps(v["n"], ensure_ascii=False)},area:{json.dumps(v["area"], ensure_ascii=False)},b:{json.dumps(v["b"])},c:"{v["c"]}",lat:{v["ll"][0]:.4f},lng:{v["ll"][1]:.4f}}},\n'
        for k, v in new_venues.items()) + "// </tm-venues>"
    rows.sort()
    rblock = "\n// <tm>  (Ticketmaster/SeatGeek feeds, fetched %s; rebuilt each update — don't edit by hand)\n" % data.get("fetched", "") + \
             "\n".join(r[3] for r in rows) + "\n// </tm>"
    # V: make sure the last hand-written entry ends with a comma before appending
    v_end = page.index("\n};", page.index("const V={"))
    head = page[:v_end].rstrip()
    if not head.endswith(",") and not head.endswith("{"):
        head += ","
    page = head + vblock + page[v_end:]
    r_end = page.index("\n];", page.index("const RAW=["))
    head = page[:r_end].rstrip()
    last_row = [l for l in head.splitlines() if l.strip() and not l.strip().startswith("//")][-1].rstrip()
    if not last_row.endswith(",") and not last_row.endswith("["):
        # add the missing comma after the last real row, not after a trailing comment
        i = head.rindex(last_row) + len(last_row)
        head = head[:i] + "," + head[i:]
    page = head + rblock + page[r_end:]
    open(page_path, "w", encoding="utf-8").write(page)
    from collections import Counter
    print(f"Ticketmaster: added {len(rows)} shows, {len(new_venues)} new venues; skipped {skipped}")
    print("by city:", dict(Counter(r[0] for r in rows)))

if __name__ == "__main__":
    main(*sys.argv[1:])

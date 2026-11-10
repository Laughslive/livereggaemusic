#!/usr/bin/env python3
"""Fetch upcoming reggae, dancehall, soca and calypso shows from Ticketmaster's Discovery API
for ReggaeLive's cities and save a compact list to data/ticketmaster.json.

Runs in GitHub Actions (see .github/workflows/ticketmaster.yml). The API key comes
from the TM_API_KEY repository secret and is never written to the repository.

How events are found: for each city, several searches run (by Ticketmaster classification
name, e.g. "Reggae", and by keyword, e.g. "soca"). An event is kept only if Ticketmaster
files it under one of the Caribbean genres/sub-genres below, or (for keyword hits) its own
name contains one of the genre words. Each kept event records which rule let it in
("why"), and the script prints a summary so the filter can be tuned.
"""
import collections, datetime, json, os, re, sys, time, urllib.parse, urllib.request

KEY = os.environ.get("TM_API_KEY")
if not KEY:
    sys.exit("TM_API_KEY is not set")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENTERS = {c["code"]: tuple(c["center"]) for c in
           json.load(open(os.path.join(_ROOT, "data", "cities.json"), encoding="utf-8"))["cities"]}
DAYS_AHEAD = 90

# Searches run for every city. classificationName matches a segment, genre or sub-genre by name.
CLASS_NAMES = ["Reggae", "Dancehall", "Soca", "Calypso", "Caribbean"]
KEYWORDS = ["reggae", "dancehall", "soca", "calypso", "sound system", "carnival fete"]

# Ticketmaster genre / sub-genre names that count (case-insensitive, whole names).
GENRES = re.compile(r"^(reggae|dancehall|soca|calypso|caribbean|dub|roots reggae|lovers rock|ragga|reggae[- ]rock|ska|rocksteady)$", re.I)
# Words in an event's own name that count for keyword hits.
NAME_WORDS = re.compile(r"\b(reggae|dancehall|soca|calypso|dub|sound ?system|sound ?clash|lovers rock|rocksteady|steel ?pan|carnival|j'?ouvert|fete)\b", re.I)

def get(params):
    url = "https://app.ticketmaster.com/discovery/v2/events.json?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 + attempt * 2); continue
            raise
    raise RuntimeError("rate limited")

def classes(e):
    """All genre / sub-genre names Ticketmaster gives the event and its performers."""
    names = []
    for c in (e.get("classifications") or []):
        for lvl in ("genre", "subGenre"):
            n = (c.get(lvl) or {}).get("name")
            if n and n.lower() != "undefined": names.append(n)
    for a in e.get("_embedded", {}).get("attractions", []) or []:
        for c in (a.get("classifications") or []):
            for lvl in ("genre", "subGenre"):
                n = (c.get(lvl) or {}).get("name")
                if n and n.lower() != "undefined": names.append(n)
    return names

def keep(e, how):
    hits = [n for n in classes(e) if GENRES.match(n.strip())]
    if hits:
        return "class:" + hits[0]
    if how.startswith("keyword") and NAME_WORDS.search(e.get("name") or ""):
        return "name:" + NAME_WORDS.search(e["name"]).group(0).lower()
    return None

def main():
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    end = now + datetime.timedelta(days=DAYS_AHEAD)
    seen, out = set(), []
    stats, dropped = collections.Counter(), collections.Counter()
    searches = [("class", {"classificationName": n}) for n in CLASS_NAMES] + \
               [("keyword", {"keyword": k}) for k in KEYWORDS]
    for code, (lat, lng) in CENTERS.items():
        n = 0
        for how, extra in searches:
            page = 0
            while True:
                data = get({"apikey": KEY, "latlong": f"{lat},{lng}", "radius": 50, "unit": "miles",
                            "size": 200, "page": page, "sort": "date,asc", "segmentName": "Music",
                            "startDateTime": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "endDateTime": end.strftime("%Y-%m-%dT%H:%M:%SZ"), **extra})
                time.sleep(0.25)
                for e in data.get("_embedded", {}).get("events", []):
                    st = e.get("dates", {}).get("start", {})
                    if not st.get("localDate") or not st.get("localTime") or e["id"] in seen:
                        continue
                    why = keep(e, how)
                    if not why:
                        dropped[" / ".join(sorted(set(classes(e)))) or "(none)"] += 1
                        continue
                    seen.add(e["id"]); n += 1; stats[why] += 1
                    v = (e.get("_embedded", {}).get("venues") or [{}])[0]
                    loc = v.get("location") or {}
                    pr = (e.get("priceRanges") or [{}])[0]
                    out.append({
                        "city": code, "id": e["id"], "name": e.get("name"),
                        "date": st["localDate"], "time": st["localTime"][:5],
                        "status": e.get("dates", {}).get("status", {}).get("code"),
                        "venue": v.get("name"), "venueCity": (v.get("city") or {}).get("name"),
                        "state": (v.get("state") or {}).get("stateCode"), "address": (v.get("address") or {}).get("line1"),
                        "lat": float(loc["latitude"]) if loc.get("latitude") else None,
                        "lng": float(loc["longitude"]) if loc.get("longitude") else None,
                        "url": e.get("url"), "priceMin": pr.get("min"), "priceMax": pr.get("max"),
                        "genres": sorted(set(classes(e))), "why": why,
                        "attractions": [a.get("name") for a in e.get("_embedded", {}).get("attractions", [])],
                        "ageRestricted": bool((e.get("ageRestrictions") or {}).get("legalAgeEnforced")),
                    })
                pg = data.get("page", {})
                page += 1
                if page >= pg.get("totalPages", 0) or (page + 1) * 200 > 1000:
                    break
        print(f"{code}: {n} events")
    out.sort(key=lambda x: (x["city"], x["date"], x["time"]))
    os.makedirs("data", exist_ok=True)
    with open("data/ticketmaster.json", "w") as f:
        json.dump({"fetched": now.isoformat(), "source": "Ticketmaster Discovery API", "events": out},
                  f, ensure_ascii=False, indent=0)
    print(f"total {len(out)} events")
    print("kept because:", dict(stats.most_common()))
    print("most common classifications among skipped keyword/genre hits:", dict(dropped.most_common(15)))

if __name__ == "__main__":
    main()

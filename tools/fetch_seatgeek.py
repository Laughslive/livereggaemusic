#!/usr/bin/env python3
"""Fetch upcoming reggae, dancehall, soca, calypso and African-music shows from SeatGeek's
public Platform API for Live Reggae Music's cities and save them to data/seatgeek.json, in the same
shape as data/ticketmaster.json, so tools/merge_ticketmaster.py can merge both.

SeatGeek is used to FIND shows Ticketmaster misses (AXS, Eventbrite, Dice and box-office shows
often appear there). It is a resale marketplace, so its links are never shown to fans: seatgeek.com
matches LISTING_SITE in index.html, and the ticket button falls back to the venue's own site or a
search. Hand-checked rows and Ticketmaster rows always win over SeatGeek rows.

Runs in GitHub Actions. The client id comes from the SEATGEEK_CLIENT_ID repository secret.
If the secret is missing, it writes an empty list and exits normally, so the daily update still runs.
"""
import collections, datetime, json, os, re, sys, time, urllib.parse, urllib.request

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(_ROOT, "data", "seatgeek.json")
CLIENT = os.environ.get("SEATGEEK_CLIENT_ID")
CENTERS = {c["code"]: tuple(c["center"]) for c in
           json.load(open(os.path.join(_ROOT, "data", "cities.json"), encoding="utf-8"))["cities"]}
WATCH = json.load(open(os.path.join(_ROOT, "data", "watch_artists.json"), encoding="utf-8"))["artists"]
DAYS_AHEAD = 90
KEYWORDS = ["reggae", "dancehall", "soca", "calypso", "afrobeats", "amapiano"]
GENRES = re.compile(r"reggae|dancehall|soca|calypso|caribbean|dub|ska|rocksteady|african|afro|amapiano|highlife", re.I)
NAME_WORDS = re.compile(r"\b(reggae|dancehall|soca|calypso|dub|sound ?clash|lovers rock|steel ?pan|carnival|"
                        r"j'?ouvert|fete|afro ?beats?|afrobeat|amapiano|highlife|afro ?nation)\b", re.I)

def norm(x):
    return re.sub(r"[^a-z0-9]", "", (x or "").lower())

def get(params):
    params = {"client_id": CLIENT, "per_page": 100, **params}
    url = "https://api.seatgeek.com/2/events?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(3 + attempt * 3); continue
            raise
    raise RuntimeError("rate limited")

def genres(e):
    return sorted({g.get("name") or g.get("slug") for p in e.get("performers") or [] for g in p.get("genres") or []
                   if g.get("name") or g.get("slug")})

def record(e, why, extra=None):
    v = e.get("venue") or {}
    loc = v.get("location") or {}
    dt = e["datetime_local"]
    st = e.get("stats") or {}
    d = {"city": "", "id": "sg" + str(e["id"]), "name": e.get("title") or e.get("short_title"),
         "date": dt[:10], "time": dt[11:16], "status": None,
         "venue": v.get("name"), "venueCity": v.get("city"), "state": v.get("state"), "address": v.get("address"),
         "lat": loc.get("lat"), "lng": loc.get("lon"), "url": e.get("url"),
         "priceMin": None, "priceMax": None,   # SeatGeek prices are resale prices: never shown
         "genres": genres(e), "why": why, "source": "seatgeek",
         "attractions": [p.get("name") for p in e.get("performers") or []], "ageRestricted": False}
    if extra: d.update(extra)
    return d

def usable(e):
    return (e.get("datetime_local") and not e.get("time_tbd") and not e.get("date_tbd")
            and (e.get("venue") or {}).get("location"))

def main():
    if not CLIENT:
        print("SEATGEEK_CLIENT_ID is not set: skipping SeatGeek (writing an empty list)")
        json.dump({"fetched": "", "source": "SeatGeek Platform API", "events": []}, open(OUT, "w"), indent=0)
        return
    now = datetime.datetime.now()
    window = {"datetime_local.gte": now.strftime("%Y-%m-%dT00:00:00"),
              "datetime_local.lte": (now + datetime.timedelta(days=DAYS_AHEAD)).strftime("%Y-%m-%dT23:59:59")}
    seen, out, stats = set(), [], collections.Counter()
    # 1. Genre words near each city center
    for code, (lat, lng) in CENTERS.items():
        for kw in KEYWORDS:
            page = 1
            while page <= 3:
                data = get({"q": kw, "lat": lat, "lon": lng, "range": "50mi", "taxonomies.name": "concert", "page": page, **window})
                time.sleep(0.3)
                for e in data.get("events") or []:
                    if e["id"] in seen or not usable(e):
                        continue
                    g = " ".join(genres(e))
                    if GENRES.search(g):
                        why = "genre:" + GENRES.search(g).group(0).lower()
                    elif NAME_WORDS.search(e.get("title") or ""):
                        why = "name:" + NAME_WORDS.search(e["title"]).group(0).lower()
                    else:
                        stats["skipped"] += 1; continue
                    seen.add(e["id"]); stats[why] += 1
                    out.append(record(e, why))
                meta = data.get("meta") or {}
                if page * 100 >= (meta.get("total") or 0):
                    break
                page += 1
    # 2. Watch-list artists, U.S.-wide
    for art in WATCH:
        data = get({"q": art["name"], "venue.country": "US", **window})
        time.sleep(0.3)
        for e in data.get("events") or []:
            if e["id"] in seen or not usable(e):
                continue
            names = [norm(p.get("name")) for p in e.get("performers") or []]
            whole = re.search(r"(?<![a-z0-9])" + re.escape(art["name"].lower()) + r"(?![a-z0-9])", (e.get("title") or "").lower())
            short = " " not in art["name"].strip() and len(art["name"]) <= 6
            if norm(art["name"]) not in names and (art.get("performer_only") or short or not whole):
                continue
            seen.add(e["id"]); stats["artist"] += 1
            out.append(record(e, "artist:" + art["name"], {"type": art["type"]}))
    out.sort(key=lambda x: (x["date"], x["time"]))
    json.dump({"fetched": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
               "source": "SeatGeek Platform API", "events": out}, open(OUT, "w"), ensure_ascii=False, indent=0)
    print(f"total {len(out)} events; {dict(stats.most_common())}")

if __name__ == "__main__":
    main()

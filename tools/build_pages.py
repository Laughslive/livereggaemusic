#!/usr/bin/env python3
"""Build ReggaeLive's city pages, sitemap and robots.txt from index.html.

Run from the repository root after index.html has been updated:
    python3 tools/build_pages.py

It is safe to run repeatedly: blocks it inserts are wrapped in
<!--ll:NAME--> ... <!--/ll:NAME--> markers and replaced on each run.
Optional snippets (analytics, Google Search Console tag) go in
tools/head_extra.html; its contents are added to every page's <head>.
"""
import datetime, html, json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Name, domain and contact addresses live in data/site.json.
_SITE = json.load(open(os.path.join(ROOT, "data", "site.json"), encoding="utf-8"))
NAME = _SITE["name"]
SITE = "https://" + _SITE["domain"]
EMAIL_SHOWS, EMAIL_INFO = _SITE.get("email_shows", ""), _SITE.get("email_info", "")

# The city list lives in data/cities.json (shared with the Ticketmaster scripts).
_CFG = json.load(open(os.path.join(ROOT, "data", "cities.json"), encoding="utf-8"))
CITIES = [(c["code"], c["slug"], c["name"], c["short"], c["nearby"]) for c in _CFG["cities"]]
REGIONS = [(r, sorted([c["code"] for c in _CFG["cities"] if c["region"] == r],
                      key=lambda k: next(x["name"] for x in _CFG["cities"] if x["code"] == k)))
           for r in _CFG["regions"]]
BY = {c[0]: c for c in CITIES}

def block(name, content):
    return f"<!--ll:{name}-->{content}<!--/ll:{name}-->"

def put_block(page, name, content, before):
    """Replace an existing marked block, or insert it before the `before` string."""
    pat = re.compile(r"<!--ll:%s-->.*?<!--/ll:%s-->" % (name, name), re.S)
    new = block(name, content)
    if pat.search(page):
        return pat.sub(lambda m: new, page, count=1)
    i = page.index(before)
    return page[:i] + new + "\n" + page[i:]

def strip_blocks(page):
    return re.sub(r"<!--ll:(\w+)-->.*?<!--/ll:\1-->\n?", "", page, flags=re.S)

def city_shows():
    """Run the page's own data code in node and return upcoming shows per city."""
    src = strip_blocks(open(os.path.join(ROOT, "index.html"), encoding="utf-8").read())
    start = src.rindex("<script>") + len("<script>")
    js = src[start: src.rindex("</script>")]
    js = js[: js.index("function render")]
    js += r"""
const out={};
for(const c in CENTER){
  out[c]=SHOWS.filter(s=>miles(CENTER[c],[s.v.lat,s.v.lng])<=RADIUS&&s.d>=todayStr)
    .sort((a,b)=>(a.d+a.t).localeCompare(b.d+b.t)).slice(0,40)
    .map(s=>({d:s.d,t:s.t,title:s.title,who:s.who,venue:s.v.n,area:s.v.area,b:s.v.b}));
}
console.log(JSON.stringify(out));
"""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(js)
        path = f.name
    try:
        return json.loads(subprocess.check_output(["node", path], text=True))
    finally:
        os.unlink(path)

def fmt_when(d, t):
    dt = datetime.datetime.strptime(d + " " + t, "%Y-%m-%d %H:%M")
    return dt.strftime("%a, %b ") + str(dt.day) + " · " + dt.strftime("%I:%M %p").lstrip("0")

def static_list(code, shows):
    name = BY[code][2]
    items = "".join(
        f"<li><b>{html.escape(s['title'])}</b> — {fmt_when(s['d'], s['t'])} — "
        f"{html.escape(s['venue'])}, {html.escape(s['area'])}</li>" for s in shows)
    return (f'<section class="seo-list"><h2>Upcoming reggae, dancehall, soca &amp; afrobeats shows in {html.escape(name)}</h2>'
            f"<ul>{items}</ul></section>")

def nav_html(current=None):
    groups = []
    for region, codes in REGIONS:
        links = " · ".join(
            (f"<b>{html.escape(BY[c][2])}</b>" if c == current else
             f'<a href="/{BY[c][1]}/">{html.escape(BY[c][2])}</a>') for c in codes)
        groups.append(f"<p><span>{region}:</span> {links}</p>")
    home = "" if current is None else ' · <a href="/">All cities</a>'
    sub = ""
    if EMAIL_SHOWS:
        href = (f"mailto:{EMAIL_SHOWS}?subject=Show%20submission&body=Artist(s)%3A%0AVenue%3A%0ACity%3A%0A"
                "Date%20and%20time%3A%0ATicket%20link%3A%0A")
        sub = f' · <a href="{href}">Submit a show</a>'
    groups.append(f'<p class="sitelinks"><a href="/about/">About &amp; contact</a>{sub}'
                  ' · <a href="/privacy/">Privacy</a></p>')
    return ('<nav class="citylinks" aria-label="Shows by city"><style>'
            ".citylinks{margin-top:36px;font-size:14px;color:var(--muted)}"
            ".citylinks h2{font-size:15px;margin:0 0 6px;color:var(--ink)}"
            ".citylinks p{margin:4px 0}.citylinks span{font-weight:600}"
            ".citylinks a{color:var(--accent)}.citylinks b{color:var(--ink)}"
            ".citylinks .sitelinks{margin-top:12px;padding-top:10px;border-top:1px solid var(--line)}"
            f"</style><h2>Reggae shows by city{home}</h2>{''.join(groups)}</nav>")

def head_html(title, desc, url):
    extra = ""
    p = os.path.join(ROOT, "tools", "head_extra.html")
    if os.path.exists(p):
        extra = open(p, encoding="utf-8").read().strip()
    e = html.escape
    return (f'<link rel="canonical" href="{url}">'
            f'<meta property="og:type" content="website"><meta property="og:site_name" content="{e(NAME)}">'
            f'<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">'
            f'<meta property="og:url" content="{url}"><meta name="twitter:card" content="summary">'
            '<link rel="manifest" href="/manifest.webmanifest"><meta name="theme-color" content="#0C1410">'
            '<link rel="icon" type="image/png" sizes="32x32" href="/icons/favicon-32.png">'
            '<link rel="icon" type="image/png" sizes="192x192" href="/icons/icon-192.png">'
            '<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">'
            '<meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes">'
            f'<meta name="apple-mobile-web-app-title" content="{e(NAME)}">'
            '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">'
            '<script>window.LL_SITE=1;if("serviceWorker"in navigator)addEventListener("load",()=>navigator.serviceWorker.register("/sw.js").catch(()=>{}))</script>'
            '<script defer src="/install.js"></script>'
            f"{extra}")

STATIC_PAGES = [
    ("about", f"About {NAME}: Where Our Reggae Listings Come From",
     f"{NAME} lists reggae, dancehall, soca, calypso and afrobeats shows in 34 U.S. cities, from venues' and promoters' own pages, artists' tour pages and Ticketmaster."),
    ("privacy", f"Privacy | {NAME}",
     f"{NAME} has no accounts and sets no cookies. What the site stores on your device and the cookie-free analytics it uses."),
]
STATIC_CSS = """:root{--bg:#0C1410;--surface:#13201A;--ink:#F4F1E1;--muted:#A8B5A2;--line:#24392D;--accent:#FFC233;--bulb:#2FCB73;--red:#E5483B;--on-accent:#141006;
--display:"Rubik Mono One","Arial Black",Impact,sans-serif;--body:"Figtree",system-ui,-apple-system,"Segoe UI",sans-serif;color-scheme:dark}
*{box-sizing:border-box}html{background:var(--bg)}
body{margin:0;background:var(--bg) radial-gradient(60rem 28rem at 15% -10%,color-mix(in srgb,var(--accent) 16%,transparent),transparent 70%) no-repeat;
color:var(--ink);font:16px/1.6 var(--body);padding:0 max(16px,env(safe-area-inset-left,0px)) 48px}
.wrap{max-width:720px;margin:0 auto}header{padding:28px 0 8px;display:grid;gap:12px}
.bulbs{display:flex;width:132px;height:6px;border-radius:3px;overflow:hidden}.bulbs i{flex:1;background:var(--bulb)}
.bulbs i:nth-child(3n+1){background:var(--red)}.bulbs i:nth-child(3n+2){background:var(--accent)}
.logo{font-family:var(--display);font-size:clamp(26px,6vw,38px);line-height:1;margin:0;color:var(--ink);text-decoration:none;
}
.logo .onair{display:inline-block;margin-left:.08em;padding:.06em .2em .04em;border-radius:.14em;font-size:.82em;
background:var(--accent);color:var(--on-accent)}
main h1{font-family:var(--display);font-weight:400;font-size:clamp(24px,5vw,32px);line-height:1.15;margin:22px 0 8px}
main h2{font-size:19px;margin:28px 0 6px}main p,main li{color:var(--ink)}main .lead{font-size:18px}
main .small{color:var(--muted);font-size:14px}main ul{padding-left:22px}main li{margin:6px 0}
a{color:var(--accent)}a:focus-visible{outline:3px solid var(--bulb);outline-offset:2px}
footer{margin-top:28px;color:var(--muted);font-size:13px}"""

def fill_emails(body):
    """<!--if:shows-->…<!--/if--> sections appear only when that address is set in data/site.json;
    {{SHOWS}} and {{INFO}} become mailto links."""
    for key, addr in (("shows", EMAIL_SHOWS), ("info", EMAIL_INFO)):
        body = re.sub(r"<!--if:%s-->(.*?)<!--/if-->" % key, (lambda m: m.group(1)) if addr else "", body, flags=re.S)
    body = body.replace("{{SHOWS}}", f'<a href="mailto:{EMAIL_SHOWS}?subject=Show%20submission">{EMAIL_SHOWS}</a>')
    body = body.replace("{{INFO}}", f'<a href="mailto:{EMAIL_INFO}">{EMAIL_INFO}</a>')
    return body.replace("{{NAME}}", NAME)

def static_page(title, desc, url, body):
    e = html.escape
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f'<title>{e(title)}</title>\n<meta name="description" content="{e(desc)}">\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rubik+Mono+One&family=Figtree:wght@400;500;600;700&display=swap">\n'
            f"<style>{STATIC_CSS}</style>\n" + block("head", head_html(title, desc, url)) + "\n</head>\n<body>\n<div class=\"wrap\">\n"
            '<header><div class="bulbs" aria-hidden="true"><i></i><i></i><i></i></div>'
            '<a class="logo" href="/">Reggae<span class="onair">Live</span></a></header>\n'
            f"<main>\n{body}\n</main>\n" + block("nav", nav_html("_static")) +
            f"\n<footer>{NAME} · reggae, dancehall, soca &amp; afrobeats near you</footer>\n</div>\n</body>\n</html>\n")

def set_title_desc(page, title, desc):
    page = re.sub(r"<title>.*?</title>", lambda m: f"<title>{html.escape(title)}</title>", page, count=1, flags=re.S)
    page = re.sub(r'<meta name="description" content="[^"]*">',
                  lambda m: f'<meta name="description" content="{html.escape(desc)}">', page, count=1)
    return page

def check_page(page):
    """Make sure the page's own code knows every city in data/cities.json (and no others)."""
    problems = []
    js = page[page.rindex("<script>"):]
    centers = set(re.findall(r"\b([A-Z]{2,3}):\[-?\d", js[js.index("const CENTER="):]))
    names = re.search(r"const CITY_NAME=\{(.*?)\};", js, re.S)
    slugs = re.search(r"const CITY_SLUG=\{(.*?)\};", js, re.S)
    opts = set(re.findall(r'<option value="([A-Z]{2,3})"', page))
    for code, slug, name, short, nearby in CITIES:
        if code not in centers: problems.append(f"{code}: missing from CENTER")
        if not names or not re.search(r"\b%s:\"" % code, names.group(1)): problems.append(f"{code}: missing from CITY_NAME")
        if not slugs or f'{code}:"{slug}"' not in slugs.group(1): problems.append(f"{code}: CITY_SLUG should be \"{slug}\"")
        if code not in opts: problems.append(f"{code}: missing from the city dropdown")
        if not re.search(r"\[%s_PLACES,\"%s\"\]" % (code, code), js) and code not in ("NYC", "PHL"):
            problems.append(f"{code}: no {code}_PLACES place-name table in TABLES")
    extra = opts - {c[0] for c in CITIES}
    if extra: problems.append(f"dropdown has cities not in data/cities.json: {sorted(extra)}")
    if problems:
        sys.exit("City list mismatch between data/cities.json and index.html:\n  " + "\n  ".join(problems) +
                 "\nSee tools/ADDING_A_CITY.md.")

def main():
    today = datetime.date.today().isoformat()
    index_path = os.path.join(ROOT, "index.html")
    base = strip_blocks(open(index_path, encoding="utf-8").read())
    check_page(base)
    shows = city_shows()

    # Home page
    title = f"{NAME}: Reggae, Dancehall, Soca & Afrobeats Shows Near You"
    desc = ("Find upcoming reggae, dancehall, soca, calypso and afrobeats shows near you, in cities including New York, Miami, "
            "Atlanta, Washington D.C., Boston, Philadelphia, Houston, Los Angeles and the San Francisco Bay Area.")
    home = set_title_desc(base, title, desc)
    home = put_block(home, "head", head_html(title, desc, SITE + "/"), "</head>")
    home = put_block(home, "nav", nav_html(), "<footer>")
    open(index_path, "w", encoding="utf-8").write(home)

    # City pages
    for code, slug, name, short, nearby in CITIES:
        url = f"{SITE}/{slug}/"
        n = len(shows.get(code, []))
        title = f"Reggae Shows in {short}: Reggae, Dancehall, Soca & Afrobeats | {NAME}"
        desc = (f"Upcoming reggae, dancehall, soca, calypso and afrobeats shows in {name} and within 50 miles, including {nearby}. "
                "Touring artists, sound systems and festivals, with links to the venue's or promoter's own tickets.")
        pg = set_title_desc(base, title, desc)
        pg = put_block(pg, "head", head_html(title, desc, url) + f"<script>window.LL_CITY={json.dumps(code)}</script>", "</head>")
        pg = pg.replace('<option value="NYC" selected>', '<option value="NYC">', 1)
        pg = pg.replace(f'<option value="{code}">', f'<option value="{code}" selected>', 1)
        pg = re.sub(r'(<input id="loc"[^>]*?) value="[^"]*"', r'\1 value=""', pg, count=1)
        pg = re.sub(r'<p class="tag">.*?</p>',
                    lambda m: f'<p class="tag">Reggae, dancehall, soca, calypso and afrobeats in {html.escape(name)} and up to 50 miles around it, '
                              f'from sound-system nights to arena headliners. Enter where you are to see what\'s closest.</p>',
                    pg, count=1, flags=re.S)
        pg = pg.replace('<main id="results"></main>',
                        f'<main id="results">{static_list(code, shows.get(code, []))}</main>', 1)
        pg = put_block(pg, "nav", nav_html(code), "<footer>")
        os.makedirs(os.path.join(ROOT, slug), exist_ok=True)
        open(os.path.join(ROOT, slug, "index.html"), "w", encoding="utf-8").write(pg)
        print(f"{slug}: {n} shows in static list")

    # About / Privacy pages, from tools/pages/<slug>.html
    for slug, title, desc in STATIC_PAGES:
        body = open(os.path.join(ROOT, "tools", "pages", slug + ".html"), encoding="utf-8").read()
        body = fill_emails(body)
        os.makedirs(os.path.join(ROOT, slug), exist_ok=True)
        open(os.path.join(ROOT, slug, "index.html"), "w", encoding="utf-8").write(static_page(title, desc, f"{SITE}/{slug}/", body))
        print(f"{slug}: static page")

    urls = [SITE + "/"] + [f"{SITE}/{c[1]}/" for c in CITIES] + [f"{SITE}/{p[0]}/" for p in STATIC_PAGES]
    sm = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq></url>\n" for u in urls)
          + "</urlset>\n")
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(sm)
    open(os.path.join(ROOT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    print("wrote sitemap.xml and robots.txt")

if __name__ == "__main__":
    main()

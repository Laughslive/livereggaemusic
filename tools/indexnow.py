#!/usr/bin/env python3
"""Tell IndexNow search engines (Bing, Yandex, Seznam, Naver…) that every page in sitemap.xml changed.
The key and domain come from data/site.json; the key file <key>.txt sits at the site root."""
import json, os, re, sys, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "data", "site.json"), encoding="utf-8"))
KEY, HOST = CFG["indexnow_key"], CFG["domain"]
urls = re.findall(r"<loc>(.*?)</loc>", open(os.path.join(ROOT, "sitemap.xml")).read())
body = json.dumps({"host": HOST, "key": KEY,
                   "keyLocation": f"https://{HOST}/{KEY}.txt", "urlList": urls}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                             headers={"Content-Type": "application/json; charset=utf-8"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("IndexNow response:", r.status, "for", len(urls), "pages")
except Exception as e:   # never fail the site update because of this
    print("IndexNow notice failed:", e); sys.exit(0)

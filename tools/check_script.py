#!/usr/bin/env python3
"""Fail if index.html's main app script doesn't parse (runs `node --check` on it)."""
import os, subprocess, sys, tempfile
s = open("index.html", encoding="utf-8").read()
js = s[s.rindex("<script>") + 8: s.rindex("</script>")]
with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
    f.write(js)
r = subprocess.run(["node", "--check", f.name])
os.unlink(f.name)
sys.exit(r.returncode)

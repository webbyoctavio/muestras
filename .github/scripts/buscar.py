import json, os, re, sys, time, html, urllib.request, urllib.parse
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
OUT = "tmp-fotos"
os.makedirs(f"{OUT}/meta2", exist_ok=True)

def get(url, binary=False, tries=3, wait=3):
    err = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
            with urllib.request.urlopen(req, timeout=40) as r:
                data = r.read()
                return data if binary else data.decode("utf-8", "replace")
        except Exception as e:
            err = e
            if "429" in str(e): time.sleep(45)
            else: time.sleep(wait)
    print("  fallo", url[:110], err, flush=True)
    return None

def stocksnap(q):
    out = []
    t = get("https://stocksnap.io/api/search-photos/" + urllib.parse.quote(q) + "/relevance/desc/1")
    if not t: return out
    try: d = json.loads(t)
    except Exception: return out
    for r in d.get("results", []):
        kw = [k.replace(" ", "") for k in r.get("keywords", [])]
        if len(kw) < 2: continue
        slug = f"{kw[0]}-{kw[1]}_{r['img_id']}"
        out.append({"src": "stocksnap", "id": r["img_id"], "alt": ", ".join(kw[:8]), "w": r.get("img_width"), "h": r.get("img_height"),
                    "thumb_url": f"https://cdn.stocksnap.io/img-thumbs/280h/{slug}.jpg",
                    "full_url": f"https://cdn.stocksnap.io/img-thumbs/960w/{slug}.jpg"})
    return out

def burst(q, limit=30):
    page = get("https://burst.shopify.com/photos/search?q=" + urllib.parse.quote(q))
    out = []
    if not page: return out
    for tag in re.findall(r"<img\b[^>]*>", page):
        m = re.search(r'(https://burst\.shopifycdn\.com/photos/[a-z0-9\-]+)(?:_[0-9]+x)?\.jpg', tag)
        if not m: continue
        a = re.search(r'alt="([^"]*)"', tag)
        slug = m.group(1).split("/")[-1]
        if any(o["id"] == slug for o in out): continue
        base = m.group(1) + ".jpg"
        out.append({"src": "burst", "id": slug, "alt": html.unescape(a.group(1)) if a else slug.replace("-", " "),
                    "thumb_url": base + "?width=360&format=pjpg&exif=0&iptc=0",
                    "full_url": base + "?width=1800&format=pjpg&exif=0&iptc=0"})
        if len(out) >= limit: break
    return out

if os.path.exists("queries2.txt"):
    for line in open("queries2.txt"):
        line = line.strip()
        if not line or "|" not in line: continue
        key, rest = line.split("|", 1)
        ss_q, b_q = (rest.split("|") + [""])[:2]
        mf = f"{OUT}/meta2/{key}.json"
        if os.path.exists(mf): continue
        items, seen = [], set()
        for q in [x.strip() for x in ss_q.split(";") if x.strip()]:
            for it in stocksnap(q):
                if it["id"] not in seen: seen.add(it["id"]); items.append(it)
            time.sleep(1.5)
        for q in [x.strip() for x in b_q.split(";") if x.strip()]:
            for it in burst(q):
                if it["id"] not in seen: seen.add(it["id"]); items.append(it)
            time.sleep(20)
        d = f"{OUT}/thumbs2/{key}"; os.makedirs(d, exist_ok=True)
        ok = []
        for i, it in enumerate(items):
            fn = f"{d}/{i:03d}.jpg"
            if not os.path.exists(fn):
                b = get(it["thumb_url"], binary=True, tries=2, wait=1)
                if not b: continue
                open(fn, "wb").write(b)
            it["thumb"] = fn; ok.append(it)
        json.dump(ok, open(mf, "w"), indent=1)
        print(key, "->", sum(1 for i in ok if i["src"] == "stocksnap"), "stocksnap,", sum(1 for i in ok if i["src"] == "burst"), "burst", flush=True)

if os.path.exists("full.txt"):
    os.makedirs(f"{OUT}/full", exist_ok=True)
    for line in open("full.txt"):
        p = line.split()
        if len(p) != 2: continue
        name, url = p
        fn = f"{OUT}/full/{name}.jpg"
        if os.path.exists(fn): continue
        b = get(url, binary=True)
        if b: open(fn, "wb").write(b)
        time.sleep(0.3)
    print("full:", len(os.listdir(f"{OUT}/full")))

import json, os, re, sys, time, html, urllib.request, urllib.parse
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
OUT = "tmp-fotos"
os.makedirs(f"{OUT}/meta", exist_ok=True)

def get(url, binary=False, tries=2):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9", "Accept": "text/html,application/xhtml+xml,image/avif,image/webp,*/*"})
            with urllib.request.urlopen(req, timeout=40) as r:
                data = r.read()
                return data if binary else data.decode("utf-8", "replace")
        except Exception as e:
            err = e
            time.sleep(2)
    print("  fallo", url[:100], err)
    return None

def unsplash(q):
    page = get("https://unsplash.com/s/photos/" + urllib.parse.quote(q.replace(" ", "-")) + "?license=free")
    out = []
    if not page: return out
    for tag in re.findall(r"<img\b[^>]*>", page):
        m = re.search(r'src="(https://images\.unsplash\.com/photo-[^"?]+)', tag)
        if not m: continue
        a = re.search(r'alt="([^"]*)"', tag)
        out.append({"src": "unsplash", "id": m.group(1).split("/")[-1], "base": m.group(1), "alt": html.unescape(a.group(1)) if a else ""})
    return out

def burst(q):
    page = get("https://burst.shopify.com/photos/search?utf8=%E2%9C%93&q=" + urllib.parse.quote(q))
    out = []
    if not page: return out
    for tag in re.findall(r"<img\b[^>]*>", page):
        m = re.search(r'(https://burst\.shopifycdn\.com/photos/[a-z0-9\-]+)(?:_[0-9]+x)?\.jpg', tag)
        if not m: continue
        a = re.search(r'alt="([^"]*)"', tag)
        slug = m.group(1).split("/")[-1]
        out.append({"src": "burst", "id": slug, "base": m.group(1) + ".jpg", "alt": html.unescape(a.group(1)) if a else slug.replace("-", " ")})
    return out

def thumb_url(it, w=420):
    if it["src"] == "unsplash":
        return it["base"] + f"?w={w}&q=60&fm=jpg&fit=max"
    return it["base"] + f"?width={w}&format=pjpg&exif=0&iptc=0"

if os.path.exists("queries.txt"):
    for line in open("queries.txt"):
        line = line.strip()
        if not line or "|" not in line: continue
        key, q = line.split("|", 1)
        mf = f"{OUT}/meta/{key}.json"
        if os.path.exists(mf): continue
        items, seen = [], set()
        for fn in (unsplash, burst):
            for it in fn(q):
                if it["id"] in seen: continue
                seen.add(it["id"]); items.append(it)
            time.sleep(1)
        d = f"{OUT}/thumbs/{key}"; os.makedirs(d, exist_ok=True)
        for i, it in enumerate(items):
            fn = f"{d}/{i:02d}.jpg"
            if not os.path.exists(fn):
                b = get(thumb_url(it), binary=True)
                if b: open(fn, "wb").write(b)
            it["thumb"] = fn
        json.dump(items, open(mf, "w"), indent=1)
        print(key, q, "->", sum(1 for i in items if i["src"] == "unsplash"), "unsplash,", sum(1 for i in items if i["src"] == "burst"), "burst")

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
    print("full:", len(os.listdir(f"{OUT}/full")))

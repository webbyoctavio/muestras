import json, os, re, time, html, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
OUT = "tmp-fotos"; T0 = time.time()
def get(url, binary=False):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
        with urllib.request.urlopen(req, timeout=20) as r:
            d = r.read(); return d if binary else d.decode("utf-8", "replace")
    except Exception as e:
        print(f"[{time.time()-T0:4.0f}s] fallo {url[:80]} {e}", flush=True); return None
CATS = set("Coffee Fitness Yoga Business Nature Food Products Jewelry Office Computer Animals Backgrounds Textures Home Fall Technology Trees Beauty Moon Sunrise Romantic".split())
def burst(q):
    page = get("https://burst.shopify.com/photos/search?q=" + urllib.parse.quote(q))
    out = []
    if not page: return out
    for tag in re.findall(r"<img\b[^>]*>", page):
        m = re.search(r'(https://burst\.shopifycdn\.com/photos/[a-z0-9\-]+)(?:_[0-9]+x)?\.jpg', tag)
        if not m: continue
        a = re.search(r'alt="([^"]*)"', tag); alt = html.unescape(a.group(1)) if a else ""
        if not alt or alt.split()[0] in CATS and len(alt.split()) <= 2: continue
        slug = m.group(1).split("/")[-1]
        if any(o["id"] == slug for o in out): continue
        base = m.group(1) + ".jpg"
        out.append({"src": "burst", "id": slug, "alt": alt, "thumb_url": base + "?width=360&format=pjpg&exif=0&iptc=0", "full_url": base + "?width=1800&format=pjpg&exif=0&iptc=0"})
    return out[:36]
def commons(q):
    u = "https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrnamespace=6&gsrlimit=40&prop=imageinfo&iiprop=url|extmetadata|size&iiurlwidth=420&gsrsearch=" + urllib.parse.quote(q + " filetype:bitmap")
    t = get(u); out = []
    if not t: return out
    for p in json.loads(t).get("query", {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata", {})
        lic = md.get("LicenseShortName", {}).get("value", ""); art = re.sub("<[^>]+>", "", md.get("Artist", {}).get("value", ""))[:80]
        if ii.get("width", 0) < 1400: continue
        out.append({"src": "commons", "id": p["title"], "alt": p["title"][5:90] + " | " + lic + " | " + art, "lic": lic, "artist": art, "page": ii.get("descriptionurl"),
                    "thumb_url": ii.get("thumburl"), "full_url": re.sub(r"/\d+px-", "/1800px-", ii.get("thumburl", ""))})
    return out
jobs = [l.strip().split("|") for l in open("queries3.txt") if "|" in l]
res = {}
for key, src, q in jobs:
    items = burst(q) if src == "burst" else commons(q)
    res.setdefault(key, []).extend(items)
    print(f"[{time.time()-T0:4.0f}s] {src} {key} {q}: {len(items)}", flush=True)
    if src == "burst": time.sleep(25)
tasks = []
for key, items in res.items():
    d = f"{OUT}/thumbs3/{key}"; os.makedirs(d, exist_ok=True)
    for i, it in enumerate(items):
        it["thumb"] = f"{d}/{i:03d}.jpg"; tasks.append((it["thumb_url"], it["thumb"]))
def dl(a):
    u, f = a
    if os.path.exists(f) or not u: return
    b = get(u, True)
    if b and len(b) > 1500: open(f, "wb").write(b)
with ThreadPoolExecutor(12) as ex: list(ex.map(dl, tasks))
os.makedirs(f"{OUT}/meta3", exist_ok=True)
for key, items in res.items():
    json.dump([it for it in items if os.path.exists(it["thumb"])], open(f"{OUT}/meta3/{key}.json", "w"), indent=1)
print(f"[{time.time()-T0:4.0f}s] listo", flush=True)

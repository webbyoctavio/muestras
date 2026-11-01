import json, os, re, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
UA = "MuestrasBot/1.0 (https://github.com/webbyoctavio/muestras) python-urllib"
OUT = "tmp-fotos"
def get(url, binary=False):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = r.read(); return d if binary else d.decode("utf-8", "replace")
    except Exception as e:
        print("fallo", url[:90], e, flush=True); return None
def commons(q, minw=1800):
    u = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrnamespace=6&gsrlimit=50"
         "&prop=imageinfo&iiprop=url|extmetadata|size&iiurlwidth=420&gsrsearch=" + urllib.parse.quote(q + " filetype:bitmap"))
    t = get(u); out = []
    if not t: return out
    for p in json.loads(t).get("query", {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata", {})
        lic = md.get("LicenseShortName", {}).get("value", "")
        art = re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value", "")).strip()[:80]
        if ii.get("width", 0) < minw or ii.get("width", 0) < ii.get("height", 1): continue
        if not re.search(r"CC0|Public domain|CC BY 2|CC BY 3|CC BY 4|CC BY-SA", lic): continue
        th = ii.get("thumburl", "")
        out.append({"src": "commons", "id": p["title"], "alt": p["title"][5:100] + " | " + lic + " | " + art, "lic": lic, "artist": art,
                    "page": ii.get("descriptionurl"), "w": ii.get("width"), "h": ii.get("height"),
                    "thumb_url": th, "full_url": re.sub(r"/\d+px-", "/1920px-", th)})
    return out
jobs = [l.strip().split("|") for l in open("queries5.txt") if "|" in l]
res = {}
for key, q in jobs:
    items = commons(q); res.setdefault(key, []).extend(items); print(key, q, len(items), flush=True); time.sleep(1)
tasks = []
for key, items in res.items():
    seen, uniq = set(), []
    for it in items:
        if it["id"] in seen: continue
        seen.add(it["id"]); uniq.append(it)
    res[key] = uniq
    d = f"{OUT}/thumbs5/{key}"; os.makedirs(d, exist_ok=True)
    for i, it in enumerate(uniq): it["thumb"] = f"{d}/{i:03d}.jpg"; tasks.append((it["thumb_url"], it["thumb"]))
def dl(a):
    u, f = a
    b = get(u, True)
    if b and len(b) > 1500: open(f, "wb").write(b)
with ThreadPoolExecutor(8) as ex: list(ex.map(dl, tasks))
os.makedirs(f"{OUT}/meta5", exist_ok=True)
for key, items in res.items():
    json.dump([it for it in items if os.path.exists(it["thumb"])], open(f"{OUT}/meta5/{key}.json", "w"), indent=1)
print("listo")

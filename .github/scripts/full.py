import json, os, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
OUT = "tmp-fotos"
def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=40) as r: return r.read()
    except Exception as e: return None
# 1) descargas en tamaño grande, probando URLs en orden
os.makedirs(f"{OUT}/full", exist_ok=True)
jobs = [l.split() for l in open("full.txt") if l.strip()]
log = {}
try:
    from PIL import Image
except Exception:
    os.system("pip install -q pillow"); from PIL import Image
import io
def dl(p):
    name, urls = p[0], p[1:]
    for u in urls:
        b = get(u)
        if b and len(b) > 5000:
            try:
                im = Image.open(io.BytesIO(b)); im = im.convert("RGB")
                if max(im.size) > 2200: im.thumbnail((2200, 2200))
                im.save(f"{OUT}/full/{name}.jpg", quality=88)
                log[name] = [u, im.size]; return
            except Exception as e:
                continue
    log[name] = None
with ThreadPoolExecutor(10) as ex: list(ex.map(dl, jobs))
json.dump(log, open(f"{OUT}/full/_log.json", "w"), indent=1)
print("full ok", sum(1 for v in log.values() if v), "/", len(log), "| originales:", sum(1 for v in log.values() if v and "download-photo" in v[0]))
# 2) búsquedas extra en StockSnap
def stocksnap(q):
    t = get("https://stocksnap.io/api/search-photos/" + urllib.parse.quote(q) + "/relevance/desc/1")
    out = []
    try: d = json.loads(t) if t else {}
    except Exception: d = {}
    for r in d.get("results", []):
        kw = [k.replace(" ", "") for k in r.get("keywords", [])]
        if len(kw) < 2: continue
        slug = f"{kw[0]}-{kw[1]}_{r['img_id']}"
        out.append({"src": "stocksnap", "id": r["img_id"], "alt": ", ".join(kw[:8]), "thumb_url": f"https://cdn.stocksnap.io/img-thumbs/280h/{slug}.jpg", "full_url": f"https://cdn.stocksnap.io/img-thumbs/960w/{slug}.jpg"})
    return out
if os.path.exists("queries4.txt") and not os.path.exists(f"{OUT}/meta4"):
    os.makedirs(f"{OUT}/meta4", exist_ok=True)
    for line in open("queries4.txt"):
        if "|" not in line: continue
        key, qs = line.strip().split("|", 1)
        items, seen = [], set()
        for q in qs.split(";"):
            for it in stocksnap(q.strip()):
                if it["id"] not in seen: seen.add(it["id"]); items.append(it)
        d = f"{OUT}/thumbs4/{key}"; os.makedirs(d, exist_ok=True)
        def dt(a):
            i, it = a; fn = f"{d}/{i:03d}.jpg"; b = get(it["thumb_url"])
            if b and len(b) > 1500: open(fn, "wb").write(b); it["thumb"] = fn
        with ThreadPoolExecutor(12) as ex: list(ex.map(dt, enumerate(items)))
        json.dump([it for it in items if it.get("thumb")], open(f"{OUT}/meta4/{key}.json", "w"), indent=1)
        print(key, len(items))

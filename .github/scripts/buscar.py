import json, os, re, sys, time, html, urllib.request, urllib.parse, threading
from concurrent.futures import ThreadPoolExecutor
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
OUT = "tmp-fotos"
os.makedirs(f"{OUT}/meta2", exist_ok=True)
T0 = time.time()

def get(url, binary=False, tries=2):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
            with urllib.request.urlopen(req, timeout=25) as r:
                d = r.read()
                return d if binary else d.decode("utf-8", "replace")
        except Exception as e:
            if "429" in str(e) or "404" in str(e): return None
            time.sleep(1)
    return None

def stocksnap(q):
    t = get("https://stocksnap.io/api/search-photos/" + urllib.parse.quote(q) + "/relevance/desc/1")
    out = []
    try: d = json.loads(t) if t else {}
    except Exception: d = {}
    for r in d.get("results", []):
        kw = [k.replace(" ", "") for k in r.get("keywords", [])]
        if len(kw) < 2: continue
        slug = f"{kw[0]}-{kw[1]}_{r['img_id']}"
        out.append({"src": "stocksnap", "id": r["img_id"], "alt": ", ".join(kw[:8]), "w": r.get("img_width"), "h": r.get("img_height"),
                    "thumb_url": f"https://cdn.stocksnap.io/img-thumbs/280h/{slug}.jpg",
                    "full_url": f"https://cdn.stocksnap.io/img-thumbs/960w/{slug}.jpg"})
    return out

CATS = set("Coffee Fitness Yoga Business Nature Food Products Jewelry Office Computer Animals Backgrounds Textures Home Fall Technology Trees Beauty Moon Sunrise Romantic".split())
def burst(q, limit=30):
    page = get("https://burst.shopify.com/photos/search?q=" + urllib.parse.quote(q), tries=1)
    out = []
    if not page: return None
    for tag in re.findall(r"<img\b[^>]*>", page):
        m = re.search(r'(https://burst\.shopifycdn\.com/photos/[a-z0-9\-]+)(?:_[0-9]+x)?\.jpg', tag)
        if not m: continue
        a = re.search(r'alt="([^"]*)"', tag)
        alt = html.unescape(a.group(1)) if a else ""
        if alt in CATS or (alt and alt[0].isupper() and len(alt.split()) <= 2 and alt.split()[0] in CATS): continue
        slug = m.group(1).split("/")[-1]
        if any(o["id"] == slug for o in out): continue
        base = m.group(1) + ".jpg"
        out.append({"src": "burst", "id": slug, "alt": alt or slug.replace("-", " "),
                    "thumb_url": base + "?width=360&format=pjpg&exif=0&iptc=0",
                    "full_url": base + "?width=1800&format=pjpg&exif=0&iptc=0"})
        if len(out) >= limit: break
    return out

lines = [l.strip() for l in open("queries2.txt") if "|" in l] if os.path.exists("queries2.txt") else []
jobs = []
for line in lines:
    key, rest = line.split("|", 1)
    ss_q, b_q = (rest.split("|") + [""])[:2]
    jobs.append((key, [x.strip() for x in ss_q.split(";") if x.strip()], [x.strip() for x in b_q.split(";") if x.strip()]))

results = {k: [] for k, _, _ in jobs}
lock = threading.Lock()

def do_ss(job):
    key, qs, _ = job
    items = []
    for q in qs:
        items += stocksnap(q)
        time.sleep(0.4)
    with lock: results[key] += items
    print(f"[{time.time()-T0:5.0f}s] stocksnap {key}: {len(items)}", flush=True)

def do_burst_all():
    for key, _, bqs in jobs:
        for q in bqs:
            r = burst(q)
            if r is None:
                print(f"[{time.time()-T0:5.0f}s] burst {key}: fallo, reintento en 30s", flush=True)
                time.sleep(30); r = burst(q) or []
            with lock: results[key] += r
            print(f"[{time.time()-T0:5.0f}s] burst {key}: {len(r)}", flush=True)
            time.sleep(12)

bt = threading.Thread(target=do_burst_all); bt.start()
with ThreadPoolExecutor(4) as ex: list(ex.map(do_ss, jobs))
bt.join()

def dl(args):
    url, fn = args
    if os.path.exists(fn): return True
    b = get(url, binary=True)
    if b and len(b) > 1500: open(fn, "wb").write(b); return True
    return False

tasks = []
for key, items in results.items():
    seen, uniq = set(), []
    for it in items:
        if it["id"] in seen: continue
        seen.add(it["id"]); uniq.append(it)
    d = f"{OUT}/thumbs2/{key}"; os.makedirs(d, exist_ok=True)
    for i, it in enumerate(uniq):
        it["thumb"] = f"{d}/{i:03d}.jpg"; tasks.append((it["thumb_url"], it["thumb"]))
    results[key] = uniq
with ThreadPoolExecutor(16) as ex: ok = list(ex.map(dl, tasks))
for key, items in results.items():
    items = [it for it in items if os.path.exists(it["thumb"])]
    json.dump(items, open(f"{OUT}/meta2/{key}.json", "w"), indent=1)
print(f"[{time.time()-T0:5.0f}s] thumbs ok {sum(ok)}/{len(ok)}", flush=True)

if os.path.exists("full.txt"):
    os.makedirs(f"{OUT}/full", exist_ok=True)
    ft = []
    for line in open("full.txt"):
        p = line.split()
        if len(p) == 2: ft.append((p[1], f"{OUT}/full/{p[0]}.jpg"))
    with ThreadPoolExecutor(8) as ex: r = list(ex.map(dl, ft))
    print("full:", sum(r), "/", len(r))

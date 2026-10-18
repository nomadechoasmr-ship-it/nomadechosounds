"""Fetch the channel RSS feed, merge new long-form videos into data/videos.json,
and render library/index.html. Shorts are skipped. Safe to run repeatedly."""
import html, json, re, sys, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "videos.json"
OUT = ROOT / "library" / "index.html"
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "media": "http://search.yahoo.com/mrss/"}

SECTIONS = [
    ("tinnitus", "Tinnitus relief", r"tinnitus"),
    ("rain", "Rain", r"\brain"),
    ("birds", "Birds", r"\bbird"),
    ("noise", "White, pink and brown noise from real water", r"\bnoise"),
    ("water", "Streams, rivers and water", r"stream|river|brook|creek|water|wave|spring|waterfall|lake|marsh|shore|drop"),
    ("scenes", "Mountain and forest scenes", r"4k|forest|mountain|meadow|walk|pov|valley|snow"),
]
OTHER = ("more", "More recordings")

def is_short(entry):
    link = entry.find("a:link", NS)
    return link is not None and "/shorts/" in (link.get("href") or "")

def fetch(channel_id):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (library updater)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        root = ET.fromstring(r.read())
    out = []
    for e in root.findall("a:entry", NS):
        if is_short(e):
            continue
        vid = e.findtext("yt:videoId", namespaces=NS)
        title = e.findtext("a:title", namespaces=NS) or ""
        pub = (e.findtext("a:published", namespaces=NS) or "")[:10]
        if vid:
            out.append({"id": vid, "title": title.strip(), "published": pub})
    return out

def section_of(title):
    t = title.lower()
    for key, name, pat in SECTIONS:
        if re.search(pat, t):
            return key, name
    return OTHER

INTROS = {
    "tinnitus": "Steady water recordings chosen and measured for even loudness, with no sudden peaks.",
    "rain": "Rain with video was recorded under a roof in the Tian Shan foothills; the black-screen rain tracks were recorded from a window at home in the city.",
    "birds": "Birdsong recorded on location. Best for daytime or a short wind-down session.",
    "noise": "White, pink, brown and other noise colours shaped from our own water recordings, not generated from scratch.",
    "water": "Mountain streams and rivers are recorded in the Tian Shan above Almaty. Lake waves and shore sounds are recorded on the Kapchagay reservoir.",
    "scenes": "Visual recordings from the Tian Shan mountains.",
    "more": "Other recordings from the channel.",
}

def card(v):
    vid = html.escape(v["id"]); title = html.escape(v["title"])
    return (f'<div class="video"><button class="thumb lite" type="button" data-id="{vid}" aria-label="Play: {title}">'
            f'<img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="" loading="lazy" width="480" height="360">'
            f'<span class="play" aria-hidden="true">▶</span></button>'
            f'<div class="info"><b>{title}</b><span><a href="https://www.youtube.com/watch?v={vid}">Watch on YouTube</a></span></div></div>')

def render(videos):
    groups = {}
    for v in sorted(videos, key=lambda x: x.get("published", ""), reverse=True):
        key, name = section_of(v["title"])
        groups.setdefault((key, name), []).append(v)
    order = [(k, n) for k, n, _ in SECTIONS] + [OTHER]
    parts = []
    for k, n in order:
        if (k, n) in groups:
            items = "\n      ".join(card(v) for v in groups[(k, n)])
            parts.append(f'    <section id="{k}">\n    <h2>{html.escape(n)}</h2>\n    <p>{html.escape(INTROS.get(k, ""))}</p>\n    <div class="videos">\n      {items}\n    </div>\n    </section>')
    nav = " · ".join(f'<a href="#{k}">{html.escape(n)}</a>' for k, n in order if (k, n) in groups)
    tpl = (ROOT / "scripts" / "library_template.html").read_text(encoding="utf-8")
    return (tpl.replace("{{COUNT}}", str(len(videos)))
               .replace("{{NAV}}", nav)
               .replace("{{SECTIONS}}", "\n".join(parts)))

def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    known = {v["id"]: v for v in data["videos"]}
    if "--no-fetch" not in sys.argv:
        try:
            for v in fetch(data["channel_id"]):
                if v["id"] in known:
                    known[v["id"]].update({k: v[k] for k in ("title", "published") if v.get(k)})
                else:
                    known[v["id"]] = v
        except Exception as exc:
            print("feed fetch failed:", exc)
    data["videos"] = list(known.values())
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT.write_text(render(data["videos"]), encoding="utf-8")
    print("videos:", len(data["videos"]))

if __name__ == "__main__":
    main()

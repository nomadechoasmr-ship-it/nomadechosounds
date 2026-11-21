"""Add schema.org VideoObject markup to every page in the built site that embeds
our YouTube videos. Runs at deploy time on _site/, so new articles get it automatically.

Only videos listed in data/videos.json are marked up (that is where the real
title and upload date come from). Shorts and other unknown IDs are skipped.
Pages that already contain VideoObject are left alone.

Usage: python scripts/add_video_schema.py _site
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "_site"
BASE = "https://nomadechosounds.com"
ID_RE = re.compile(r'(?:youtube(?:-nocookie)?\.com/embed/|data-id=")([A-Za-z0-9_-]{11})')

videos = {v["id"]: v for v in json.loads((ROOT / "data" / "videos.json").read_text(encoding="utf-8"))["videos"]}

def video_node(v):
    vid = v["id"]
    return {
        "@type": "VideoObject",
        "@id": f"https://www.youtube.com/watch?v={vid}",
        "name": v["title"],
        "description": f"{v['title']}. A real field recording by Nomad Echo, not generated.",
        "thumbnailUrl": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
        "uploadDate": v["published"],
        "embedUrl": f"https://www.youtube.com/embed/{vid}",
        "url": f"https://www.youtube.com/watch?v={vid}",
    }

pages = 0
total = 0
for page in sorted(SITE.rglob("*.html")):
    s = page.read_text(encoding="utf-8")
    if "VideoObject" in s or "</head>" not in s:
        continue
    ids = []
    for vid in ID_RE.findall(s):
        if vid in videos and vid not in ids and videos[vid].get("published"):
            ids.append(vid)
    if not ids:
        continue
    rel = page.relative_to(SITE).as_posix()
    url = BASE + "/" + (rel[:-len("index.html")] if rel.endswith("index.html") else rel)
    nodes = [video_node(videos[v]) for v in ids]
    if len(nodes) > 6:
        graph = {"@context": "https://schema.org", "@type": "ItemList", "@id": url + "#videos",
                 "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": n} for i, n in enumerate(nodes)]}
    else:
        graph = {"@context": "https://schema.org", "@graph": nodes}
    tag = '<script type="application/ld+json">' + json.dumps(graph, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>\n"
    page.write_text(s.replace("</head>", tag + "</head>", 1), encoding="utf-8")
    pages += 1; total += len(nodes)
print(f"VideoObject: {total} videos on {pages} pages")

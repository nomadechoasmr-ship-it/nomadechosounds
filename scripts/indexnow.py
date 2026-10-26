"""Tell Bing (and other IndexNow engines) about pages changed recently.

Reads sitemap.xml and submits every URL whose <lastmod> is today or yesterday.
The key file lives in the site root as <key>.txt. Runs after each deploy."""
import datetime, json, re, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = "nomadechosounds.com"


def main():
    keys = [p.stem for p in ROOT.glob("*.txt") if re.fullmatch(r"[0-9a-f]{32}", p.stem)]
    if not keys:
        print("no IndexNow key file"); return
    key = keys[0]
    today = datetime.date.today()
    recent = {today.isoformat(), (today - datetime.timedelta(days=1)).isoformat()}
    xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    urls = [loc for loc, mod in re.findall(r"<loc>([^<]+)</loc><lastmod>([^<]+)</lastmod>", xml) if mod in recent]
    if not urls:
        print("nothing changed recently"); return
    body = json.dumps({"host": HOST, "key": key, "keyLocation": f"https://{HOST}/{key}.txt", "urlList": urls}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("IndexNow", r.status, len(urls), "urls")
    except Exception as exc:  # never fail the deploy over this
        print("IndexNow failed:", exc)
    for u in urls:
        print(" ", u)


if __name__ == "__main__":
    main()

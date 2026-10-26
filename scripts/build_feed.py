"""Build feed.xml (RSS 2.0) from the articles listed in sitemap.xml.

Pinterest's "auto-publish from RSS" turns each item into a Pin: it takes the
title, description, link and the image in <enclosure>/<media:content>.
Pinterest prefers tall images with a headline on them, so each item gets a
1000x1500 pin image (photo + title) generated into /assets/pins/.

Runs in the deploy workflow, so every new article lands in the feed with no
manual step. Safe to run repeatedly."""
import datetime, email.utils, html, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://nomadechosounds.com"
SKIP = {"/", "/about/", "/library/", "/privacy/"}  # not articles
FONTS = ROOT / "scripts" / "fonts"
# Optional per-page pin settings: a different photo than the page's share image
# (so pins don't all look alike) and a short line with the key number.
PINS = {
    "/nature-sound-measurements/": ("big-almaty-stone-moss", "Mountain brook 0.31 dB vs birdsong 3.73 dB"),
    "/tinnitus-masking-sounds/": ("big-almaty-stream-foam", "We measured real mountain water"),
    "/birdsong-for-sleep/": ("tian-shan-spruce-blue-sky", "42 loud events every minute"),
    "/recordings/mountain-brook/": ("big-almaty-clear-pebbles", "0.31 dB loudness variation"),
    "/recordings/mountain-river/": ("big-almaty-cascade", "Loud but constant: 0.62 dB"),
    "/tian-shan-field-recordings/": ("big-almaty-gorge-autumn-stream", "Big Almaty gorge, 1,466 m"),
}
# Bump when a page's pin image changes: Pinterest only publishes items with a
# new <guid>, so a new version makes it post the fresh pin (old pin stays).
PIN_VERSION = {
    "/nature-sound-measurements/": 2, "/tinnitus-masking-sounds/": 2,
    "/recordings/mountain-brook/": 2, "/recordings/mountain-river/": 2,
    "/tian-shan-field-recordings/": 2, "/birdsong-for-sleep/": 2,
}
# Extra pins for the same article with a different photo and subtitle
# (Pinterest favours several fresh pins per URL). (path, tag, photo, subtitle)
PIN_EXTRA = [
    ("/tinnitus-masking-sounds/", "b", "gorge-clear-pool-ripples", "Steady water, measured in decibels"),
    ("/tian-shan-field-recordings/", "b", "kapchagay-turquoise-red-rocks", "Kapchagay reservoir, Kazakhstan"),
    ("/tian-shan-field-recordings/", "c", "mossy-spring-drops-macro", "A secret mossy spring in the Tian Shan"),
    ("/recordings/mountain-river/", "b", "gorge-sunlit-cascade", "Real mountain water, no AI audio"),
    ("/nature-sound-measurements/", "b", "kapchagay-waves-red-gravel", "Waves, brooks and birds, measured"),
]
# Drip queue: extra pins released a few per day so Pinterest sees a steady
# trickle instead of a burst from a new account. The feed is rebuilt every day
# by the scheduled deploy; each entry appears on its release date.
# (path, tag, photo, subtitle) -- tags must be unique per path.
DRIP_START = datetime.date(2026, 10, 27)
DRIP_PER_DAY = 2
PIN_DRIP = [
    ("/tinnitus-masking-sounds/", "d1", "gorge-waterfall-foam", "Brook 0.31 dB vs birdsong 3.73 dB"),
    ("/tian-shan-field-recordings/", "d1", "kapchagay-zoom-h5-in-water", "A recorder standing in the lake"),
    ("/recordings/mountain-brook/", "d1", "gorge-mossy-rock-pool", "Zero sudden peaks above 6 dB"),
    ("/birdsong-for-sleep/", "d1", "tian-shan-spruce-meadow-stream", "Why a dawn chorus keeps you awake"),
    ("/nature-sound-measurements/", "d1", "clear-shallows-ripples", "Open data: download the CSV"),
    ("/recordings/mountain-river/", "d1", "gorge-stream-setup-mossy-boulders", "20 minutes measured, 0.6 dB drift"),
    ("/tian-shan-field-recordings/", "d2", "mossy-pipe-setup", "The old pipe spring in the moss"),
    ("/tinnitus-masking-sounds/", "d2", "kapchagay-lake-waves", "Steady water vs sudden sounds"),
    ("/recordings/mountain-brook/", "d2", "gorge-tripod-stream", "How we measured a mountain brook"),
    ("/birdsong-for-sleep/", "d2", "ile-alatau-spruce-snow-peaks", "Birdsong vs a mountain brook, measured"),
    ("/tian-shan-field-recordings/", "d3", "recorder-tall-grass", "Recording in the long grass"),
    ("/recordings/mountain-river/", "d2", "gorge-cliff-setup", "Recorded at a good level: -6.2 dBFS peak"),
    ("/nature-sound-measurements/", "d2", "kapchagay-gravel-shore-setup", "Every take is measured before use"),
    ("/tian-shan-field-recordings/", "d4", "kapchagay-red-rock-bay", "Red rocks of the Kapchagay shore"),
]
DEFAULT_SUB = "Real field recordings from the Tian Shan"


def wrap(draw, text, font, width):
    lines, line = [], ""
    for word in text.split():
        test = (line + " " + word).strip()
        if draw.textlength(test, font=font) <= width or not line:
            line = test
        else:
            lines.append(line); line = word
    return lines + [line]


def make_pin(slug, photo, title, sub):
    """1000x1500 pin: photo on top, night panel with headline below."""
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    W, H, PH = 1000, 1500, 860
    img = Image.new("RGB", (W, H), "#121b2c")
    src = Image.open(ROOT / "assets" / "img" / f"{photo}.jpg").convert("RGB")
    img.paste(ImageOps.fit(src, (W, PH), Image.LANCZOS, centering=(0.5, 0.45)), (0, 0))
    d = ImageDraw.Draw(img)
    pad = 70
    label = ImageFont.truetype(str(FONTS / "ibm-plex-sans-latin-600-normal.woff"), 30)
    d.text((pad, PH + 50), "NOMAD ECHO SOUNDS", font=label, fill="#8cc3dc")
    title = title[:1].upper() + title[1:]
    for size in (76, 68, 60, 54):
        head = ImageFont.truetype(str(FONTS / "gloock-latin-400-normal.woff"), size)
        lines = wrap(d, title, head, W - 2 * pad)
        if len(lines) <= 4:
            break
    y = PH + 105
    for ln in lines:
        d.text((pad, y), ln, font=head, fill="#e8ecf3"); y += int(size * 1.15)
    body = ImageFont.truetype(str(FONTS / "ibm-plex-sans-latin-400-normal.woff"), 36)
    for ln in wrap(d, sub, body, W - 2 * pad)[:2]:
        d.text((pad, y + 18), ln, font=body, fill="#9aa7bd"); y += 46
    d.text((pad, H - 80), "nomadechosounds.com", font=label, fill="#e8ecf3")
    out = ROOT / "assets" / "pins" / f"{slug}.jpg"
    out.parent.mkdir(exist_ok=True)
    img.save(out, quality=86, optimize=True, progressive=True)
    return out


def page_info(url, extra=None):
    path = url.replace(SITE, "") or "/"
    if path in SKIP:
        return None
    f = ROOT / path.strip("/") / "index.html"
    if not f.exists():
        return None
    s = f.read_text(encoding="utf-8")
    og_title = re.search(r'<meta property="og:title" content="([^"]*)"', s)
    title = og_title.group(1) if og_title else re.search(r"<title>(.*?)</title>", s, re.S).group(1)
    desc = re.search(r'<meta name="description" content="([^"]*)"', s).group(1)
    img = re.search(r'<meta property="og:image" content="[^"]*/assets/share/([a-z0-9-]+)-16x9\.jpg"', s)
    date = re.search(r'"datePublished":"(\d{4}-\d{2}-\d{2})"', s)
    if not (img and date):
        return None
    photo, sub = PINS.get(path, (img.group(1), DEFAULT_SUB))
    title = html.unescape(title)
    slug = path.strip("/").replace("/", "-")
    guid = url + (f"#pin{PIN_VERSION[path]}" if path in PIN_VERSION else "")
    if extra:
        tag, photo, sub = extra
        slug, guid = f"{slug}-{tag}", f"{url}#pin-{tag}"
    try:
        pin = make_pin(slug, photo, title, sub)
        image = f"{SITE}/assets/pins/{slug}.jpg"
    except Exception as exc:  # Pillow missing: fall back to the plain photo
        print("pin image skipped:", exc)
        pin = ROOT / "assets" / "img" / f"{photo}.jpg"
        image = f"{SITE}/assets/img/{photo}.jpg"
    return {
        "title": title, "desc": html.unescape(desc), "link": url,
        "guid": guid,
        "image": image, "length": pin.stat().st_size,
        "date": datetime.datetime.fromisoformat(date.group(1) + "T09:00:00+05:00"),
    }


def main():
    xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    urls = re.findall(r"<loc>([^<]+)</loc>", xml)
    items = [i for i in (page_info(u) for u in urls) if i]
    for path, tag, photo, sub in PIN_EXTRA:
        if SITE + path in urls:
            i = page_info(SITE + path, (tag, photo, sub))
            if i:
                items.append(i)
    today = datetime.datetime.now(datetime.timezone.utc).date()
    for n, (path, tag, photo, sub) in enumerate(PIN_DRIP):
        release = DRIP_START + datetime.timedelta(days=n // DRIP_PER_DAY)
        if release <= today and SITE + path in urls:
            i = page_info(SITE + path, (tag, photo, sub))
            if i:
                i["date"] = datetime.datetime.fromisoformat(release.isoformat() + "T09:00:00+05:00")
                items.append(i)
    items.sort(key=lambda i: i["date"], reverse=True)
    esc = lambda t: html.escape(t, quote=False)
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/" xmlns:atom="http://www.w3.org/2005/Atom">',
           "<channel>",
           "<title>Nomad Echo Sounds</title>",
           f"<link>{SITE}/</link>",
           f'<atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>',
           "<description>Real field recordings from the Tian Shan, Kazakhstan, measured for sleep and tinnitus masking. No AI audio.</description>",
           "<language>en</language>"]
    if items:
        out.append(f"<lastBuildDate>{email.utils.format_datetime(items[0]['date'])}</lastBuildDate>")
    for i in items:
        out += ["<item>",
                f"<title>{esc(i['title'])}</title>",
                f"<link>{i['link']}</link>",
                f'<guid isPermaLink="false">{i["guid"]}</guid>',
                f"<pubDate>{email.utils.format_datetime(i['date'])}</pubDate>",
                f"<description>{esc(i['desc'])}</description>",
                f'<enclosure url="{i["image"]}" length="{i["length"]}" type="image/jpeg"/>',
                f'<media:content url="{i["image"]}" medium="image" type="image/jpeg" width="1000" height="1500"/>',
                "</item>"]
    out += ["</channel>", "</rss>", ""]
    (ROOT / "feed.xml").write_text("\n".join(out), encoding="utf-8")
    print("feed items:", len(items))


if __name__ == "__main__":
    main()

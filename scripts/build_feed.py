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
SKIP = {"/", "/about/", "/library/", "/privacy/", "/ai-data-collection/"}  # not articles
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
    "/how-to-use-masking-sounds-at-night/": ("ile-alatau-mountain-stream", "Volume a little below the ringing"),
    "/how-we-record-water-sounds/": ("kapchagay-zoom-h5-in-water", "Zoom H5 standing in the water"),
    "/best-natural-sounds-for-tinnitus/": ("big-almaty-stream-foam", "Brook 0.31 dB, river 0.62, birdsong 3.73"),
    "/brook-vs-river-vs-birdsong-sleep/": ("tian-shan-spruce-meadow-stream", "Brook, river or birdsong for sleep?"),
    "/river-sounds-for-sleep/": ("big-almaty-cascade", "A real river, 0.62 dB loudness variation"),
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
    ("/how-we-record-water-sounds/", "b", "gorge-stream-setup-mossy-boulders", "A recorder, a stone, a mountain stream"),
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

# Topic boards. Each board on Pinterest auto-publishes from its own feed
# (/feeds/<board>.xml). Pins here use search-style titles (what people type on
# Pinterest), not article titles, and spread across different pages instead of
# repeating one URL. Released 1 per day per board from BOARD_START, so the
# account posts a steady 3 pins a day. Add new rows at the end of a list to
# continue the queue. (path, tag, photo, pin title, headline on image, subtitle, description)
BOARD_START = datetime.date(2026, 11, 3)
PHOTO_BOARDS = {"tian-shan", "sleep"}  # full-photo pins; tinnitus keeps the text panel
BOARDS = {
    "tinnitus": ("Tinnitus Relief Sounds", [
        ("/tinnitus-masking-sounds/", "t1", "big-almaty-stream-foam",
         "Tinnitus Relief Sounds: Real Mountain Water, Not AI Noise",
         "Tinnitus relief sounds from real mountain water", "Recorded in the Tian Shan, measured in dB",
         "Natural sounds for tinnitus masking, recorded in the Tian Shan mountains of Kazakhstan. We measured how steady each sound is, because sudden peaks pull attention back to the ringing. Free to listen."),
        ("/how-to-use-masking-sounds-at-night/", "t1", "ile-alatau-valley-stream",
         "How to Sleep with Tinnitus: Using a Masking Sound at Night",
         "How to sleep with tinnitus", "Speaker or headphones, volume, timer",
         "A practical guide to using a masking sound at night when tinnitus keeps you awake: speaker or headphones, how loud, and whether to use a timer. Based on Tinnitus UK and NHS guidance."),
        ("/nature-sound-measurements/", "t1", "gorge-mossy-rock-pool",
         "Best Nature Sounds for Tinnitus Masking: We Measured Them",
         "Which nature sounds mask tinnitus best?", "Brook 0.31 dB vs birdsong 3.73 dB",
         "Mountain brook, river and birdsong compared by loudness variation and sudden peaks. Open data from real field recordings made near Almaty, Kazakhstan."),
        ("/recordings/mountain-brook/", "t1", "ile-alatau-mountain-stream",
         "Mountain Brook Sound for Tinnitus: Steady Water, No Sudden Peaks",
         "A steady brook for ringing ears", "Zero sudden peaks above 6 dB",
         "A mountain brook from the Tian Shan, measured: 0.31 dB loudness variation and no sudden peaks, the kind of even sound tinnitus guides recommend for masking."),
        ("/tinnitus-masking-sounds/", "t2", "mossy-spring-water-threads",
         "Natural White Noise Alternative for Tinnitus: Flowing Water",
         "A natural alternative to white noise", "Real water from the Tian Shan mountains",
         "Prefer something softer than white noise for tinnitus? Flowing mountain water is a steady natural sound. Recorded and measured by a field recordist in Kazakhstan."),
        ("/recordings/mountain-river/", "t1", "gorge-sunlit-cascade",
         "River Sounds for Tinnitus: Loud but Constant Mountain Water",
         "Loud but constant river water", "0.62 dB loudness variation",
         "A loud mountain river that barely changes in level: 0.62 dB variation over 20 minutes. A strong, even sound for masking louder tinnitus."),
        ("/tinnitus-masking-sounds/", "t3", "frame-mountain-river-mossy-boulders",
         "Rushing Mountain River Sounds for Tinnitus Relief",
         "Rushing river sounds for tinnitus", "Real water, no AI audio",
         "A rushing mountain river among mossy boulders in the Tian Shan, Kazakhstan. Real field recordings for tinnitus masking, measured for steadiness."),
        ("/how-to-use-masking-sounds-at-night/", "t2", "frame-water-drop-on-moss",
         "Tinnitus at Night: How Loud Should a Masking Sound Be?",
         "How loud should a masking sound be?", "Volume a little below the ringing",
         "How loud to play a masking sound when tinnitus keeps you awake, speaker or headphones, and whether to use a timer. Based on Tinnitus UK and NHS guidance."),
        ("/nature-sound-measurements/", "t2", "frame-clear-stream-pebbles",
         "Steady Nature Sounds for Tinnitus: Open Measurement Data",
         "Which water sound is steadiest?", "Open data, measured in dB",
         "We measured our own field recordings for loudness variation and sudden peaks. Brook, river and birdsong compared, with a downloadable CSV."),
        ("/recordings/mountain-brook/", "t2", "frame-moss-stream-red-pebbles",
         "Gentle Stream Sounds for Tinnitus: Soft Water Over Moss",
         "Soft stream water for tinnitus", "A steady Tian Shan brook",
         "A gentle mountain brook from the Tian Shan with no sudden splashes, measured at 0.31 dB loudness variation. Natural sound for tinnitus masking."),
    ]),
    "sleep": ("Nature Sounds for Sleep", [
        ("/birdsong-for-sleep/", "s1", "ile-alatau-spruce-slope",
         "Is Birdsong Good for Sleep? Why Steady Water May Work Better",
         "Is birdsong good for sleep?", "42 loud events every minute",
         "Birdsong sounds relaxing, but we measured 42 loud events a minute in a dawn chorus. Why it suits a short wind-down better than a whole night, and what to play instead."),
        ("/recordings/mountain-river/", "s1", "big-almaty-cascade",
         "River Sounds for Deep Sleep and Insomnia: Real Mountain River",
         "River sounds for deep sleep", "Recorded in the Tian Shan, Kazakhstan",
         "A real mountain river recorded near Almaty for sleep. Even, constant water with no AI audio, measured before it was published."),
        ("/recordings/mountain-brook/", "s1", "big-almaty-clear-pebbles",
         "Babbling Brook Sounds for Sleep: A Calm Mountain Stream",
         "Babbling brook sounds for sleep", "A calm stream, measured",
         "A calm babbling brook from the Tian Shan mountains for falling asleep. No sudden splashes: we measured zero peaks above 6 dB."),
        ("/tian-shan-field-recordings/", "s1", "kapchagay-lake-waves",
         "Gentle Lake Waves Sounds for Sleep: Kapchagay Shore, Kazakhstan",
         "Gentle lake waves for sleep", "Kapchagay reservoir, Kazakhstan",
         "Soft lake waves recorded on the Kapchagay shore in Kazakhstan, plus the mountain streams of the Tian Shan. Real field recordings for sleep and relaxation."),
        ("/how-to-use-masking-sounds-at-night/", "s1", "clear-shallows-ripples",
         "Sleep Sounds at Night: Speaker or Headphones, and How Loud",
         "Sleep sounds: speaker or headphones?", "Volume, timer, every night",
         "How to use a sleep sound at night: speaker or headphones, a comfortable volume and whether to use a timer. Simple tips based on Tinnitus UK and NHS guidance."),
        ("/nature-sound-measurements/", "s1", "gorge-clear-pool-ripples",
         "Calming Water Sounds for Sleep, Compared by Measurement",
         "Calming water sounds, compared", "Which one stays steady all night?",
         "Brook, river and birdsong compared by how steady they stay. Open measurement data from real nature recordings in Kazakhstan."),
        ("/recordings/mountain-brook/", "s2", "frame-mossy-stones-shallow-water",
         "Relaxing Water Sounds for Sleep: A Shallow Mountain Stream",
         "Shallow stream sounds for sleep", "Real water from the Tian Shan",
         "Clear, shallow mountain water over mossy stones, recorded in the Tian Shan near Almaty. A calm, even sound for falling asleep."),
        ("/recordings/mountain-river/", "s2", "frame-mountain-stream-boulders",
         "Mountain Stream Sounds for Sleep: Water Among Boulders",
         "Mountain stream sounds for sleep", "Steady water, measured",
         "A mountain stream rushing past boulders in the Tian Shan. Loud but constant water, recorded for sleep and measured before publishing."),
        ("/tinnitus-masking-sounds/", "s1", "frame-boulder-pool-bubbles",
         "Calm Water Sounds for Insomnia: Real, Not Generated",
         "Calm water for sleepless nights", "Real field recordings, Kazakhstan",
         "Real water sounds for nights when sleep won't come, recorded in Kazakhstan with no AI audio. How we choose steady sounds that don't wake the ear."),
        ("/how-to-use-masking-sounds-at-night/", "s2", "frame-drips-through-branches",
         "Falling Asleep to Water Sounds: Simple Tips for Every Night",
         "Falling asleep to water sounds", "Volume, speaker, timer",
         "Simple tips for falling asleep to water sounds: a comfortable volume, speaker or headphones, and when a timer helps."),
    ]),
    "tian-shan": ("Tian Shan Nature & Field Recording", [
        ("/tian-shan-field-recordings/", "n1", "big-almaty-gorge-autumn-stream",
         "Big Almaty Gorge in Autumn, Almaty, Kazakhstan",
         "Big Almaty gorge in autumn", "1,466 m, Tian Shan mountains",
         "Autumn in the Big Almaty gorge at 1,466 m, where we record mountain water for sleep and tinnitus sounds. Field notes from the Tian Shan near Almaty."),
        ("/how-we-record-water-sounds/", "n1", "kapchagay-zoom-h5-in-water",
         "Field Recording Setup: How We Record Water Sounds with a Zoom H5",
         "How we record water sounds", "Zoom H5, fur windscreen, long takes",
         "Our field recording setup for water sounds: a Zoom H5 with a fur windscreen, placed a little back from the water, long takes on quiet weekdays."),
        ("/tian-shan-field-recordings/", "n2", "kapchagay-red-rock-bay",
         "Kapchagay Reservoir, Kazakhstan: Turquoise Water and Red Rocks",
         "Kapchagay, Kazakhstan", "Turquoise water, red rocks",
         "The Kapchagay reservoir near Konaev, Almaty Region: turquoise water, red rocks and quiet waves we record for sleep sounds."),
        ("/how-we-record-water-sounds/", "n2", "mossy-spring-flex-tripod",
         "Nature Sound Recording: A Zoom H5 at a Mossy Mountain Spring",
         "Recording a mountain spring", "A flexible tripod, close to the water",
         "Recording a tiny mossy spring in the Tian Shan with a Zoom H5 on a flexible tripod. How we place the recorder for clean water sounds."),
        ("/recordings/mountain-brook/", "n3", "ile-alatau-spruce-snow-peaks",
         "Tian Shan Mountains Near Almaty: Spruce Forest and Snow Peaks",
         "Tian Shan mountains near Almaty", "Ile Alatau, Kazakhstan",
         "Spruce forest and snow peaks of the Ile Alatau, the Tian Shan range above Almaty, Kazakhstan, where our mountain stream recordings come from."),
        ("/how-we-record-water-sounds/", "n4", "mossy-spring-drops-macro",
         "A Hidden Mossy Spring in the Tian Shan Mountains",
         "A hidden mossy spring", "Water from an old pipe in the moss",
         "A secret spring in the Tian Shan: water running from an old pipe overgrown with moss. One of the places our nature sounds come from."),
        ("/tian-shan-field-recordings/", "n5", "frame-old-pipe-spring-drips",
         "An Old Rusty Pipe Turned Mountain Spring, Tian Shan",
         "An old pipe turned into a spring", "Overgrown with moss, Tian Shan",
         "Water dripping from an old Soviet-era pipe on a Tian Shan riverbank, now overgrown with moss. One of the places our nature sounds come from."),
        ("/recordings/mountain-river/", "n6", "frame-tian-shan-spruce-slope",
         "Spruce Forest on a Tian Shan Slope Near Almaty",
         "Spruce forest of the Tian Shan", "Ile Alatau, Kazakhstan",
         "Tian Shan spruce on a steep rocky slope above Almaty, Kazakhstan. The mountains where we record river and stream sounds."),
        ("/recordings/mountain-brook/", "n7", "frame-mossy-spring-water-gold",
         "Macro Water Photography: A Mossy Spring in Sunlight",
         "A mossy spring in sunlight", "Filmed while recording its sound",
         "Sunlit water running over moss at a small spring in the Tian Shan, filmed while we recorded its sound."),
    ]),
}


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


def make_photo_pin(slug, photo, title, sub):
    """1000x1500 full-bleed photo pin with a small caption over a dark fade.
    Visual pins tend to get more saves than text panels on nature boards."""
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    W, H = 1000, 1500
    img = ImageOps.fit(Image.open(ROOT / "assets" / "img" / f"{photo}.jpg").convert("RGB"),
                       (W, H), Image.LANCZOS, centering=(0.5, 0.45))
    fade = Image.new("L", (1, H))
    for y in range(H):
        fade.putpixel((0, y), max(0, min(215, int((y - H * 0.62) / (H * 0.38) * 215))))
    shade = Image.new("RGB", (W, H), "#0b111c")
    img = Image.composite(shade, img, fade.resize((W, H)))
    d = ImageDraw.Draw(img)
    pad = 70
    head = ImageFont.truetype(str(FONTS / "gloock-latin-400-normal.woff"), 64)
    body = ImageFont.truetype(str(FONTS / "ibm-plex-sans-latin-400-normal.woff"), 34)
    label = ImageFont.truetype(str(FONTS / "ibm-plex-sans-latin-600-normal.woff"), 28)
    lines = wrap(d, title[:1].upper() + title[1:], head, W - 2 * pad)[:3]
    y = H - 150 - 46 - len(lines) * 74
    for ln in lines:
        d.text((pad, y), ln, font=head, fill="#f2f4f8"); y += 74
    d.text((pad, y + 10), sub, font=body, fill="#c9d2e0")
    d.text((pad, H - 90), "nomadechosounds.com", font=label, fill="#f2f4f8")
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
    write_feed(ROOT / "feed.xml", f"{SITE}/feed.xml", "Nomad Echo Sounds", items)
    print("feed items:", len(items))
    build_boards(urls, today)


def build_boards(urls, today):
    """One feed per Pinterest board, 1 new pin per board per day."""
    for board, (name, pins) in BOARDS.items():
        items = []
        for n, (path, tag, photo, ptitle, headline, sub, desc) in enumerate(pins):
            release = BOARD_START + datetime.timedelta(days=n)
            if release > today or SITE + path not in urls:
                continue
            slug = f"{board}-{path.strip('/').replace('/', '-')}-{tag}"
            try:
                maker = make_photo_pin if board in PHOTO_BOARDS and not photo.startswith("frame-") else make_pin  # video frames are too small for full-height pins
                pin = maker(slug, photo, headline, sub)
                image = f"{SITE}/assets/pins/{slug}.jpg"
            except Exception as exc:
                print("pin image skipped:", exc)
                pin = ROOT / "assets" / "img" / f"{photo}.jpg"
                image = f"{SITE}/assets/img/{photo}.jpg"
            items.append({
                "title": ptitle, "desc": desc, "link": SITE + path,
                "guid": f"{SITE}{path}#{board}-{tag}", "image": image,
                "length": pin.stat().st_size,
                "date": datetime.datetime.fromisoformat(release.isoformat() + "T09:00:00+05:00"),
            })
        items.sort(key=lambda i: i["date"], reverse=True)
        out = ROOT / "feeds" / f"{board}.xml"
        out.parent.mkdir(exist_ok=True)
        write_feed(out, f"{SITE}/feeds/{board}.xml", f"Nomad Echo Sounds: {name}", items)
        print(f"board {board}: {len(items)} of {len(pins)} pins released")


def write_feed(path, self_url, title, items):
    esc = lambda t: html.escape(t, quote=False)
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/" xmlns:atom="http://www.w3.org/2005/Atom">',
           "<channel>",
           f"<title>{esc(title)}</title>",
           f"<link>{SITE}/</link>",
           f'<atom:link href="{self_url}" rel="self" type="application/rss+xml"/>',
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
    path.write_text("\n".join(out), encoding="utf-8")

if __name__ == "__main__":
    main()

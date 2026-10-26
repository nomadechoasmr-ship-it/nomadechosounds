# Content plan — nomadechosounds.com

Each scheduled run publishes the FIRST unchecked topic, then ticks it here with the date and URL.
Use only the facts below (they come from the owner's own measurements). Never invent numbers.
If a topic says BLOCKED, skip it. If no unblocked topic is left, publish nothing and ask the owner for new material.

## Locations confirmed by the owner
- Mountain streams and rivers: Tian Shan mountains near Almaty.
- Lake waves and shore sounds: Kapchagay reservoir shore.
- Soft Marsh Water (video JYSK0zeIStk): a small stream in marshland near the Kapchagay reservoir.
- Rain with video (under a roof): Tian Shan foothills. Black-screen rain: recorded from a window at home in the city.

- Noise tracks (white, pink, brown, grey, blue): never generated. Made from the owner's own recordings (streams; water from an old steel pipe left from Soviet-era construction (owner mentions a dam) on a Tian Shan riverbank, now sunk into the slope and overgrown with moss, feeding its own tiny stream) by equalising, filtering and taming peaks in an editor. Owner's firm principle: no generated noise.

## Rule for every new article
- Insert the Ko-fi note block (`<aside class="support">…A note from Andrey…</aside>`, copy it exactly from /tinnitus-masking-sounds/, including the photo) inside the article, right after the main "Listen" videos and before the medical note. Not only in the footer.

- SEO head for every new article (copy the <head> of /recordings/mountain-river/ and change only the page-specific values):
  - `<title>` at most 60 characters, key phrase first, no " · Nomad Echo Sounds" suffix if it pushes past 60.
  - `<meta name="description">` at most 160 characters.
  - Keep the favicon / apple-touch-icon / manifest / theme-color lines exactly as they are.
  - `og:image` = one of the 16:9 files in /assets/share/ (pick the photo that fits the topic), with og:image:width 900 / height 506.
  - JSON-LD as an `@graph`: the Article with `image` (the 16x9, 4x3 and 1x1 versions of the same photo), `author` = the Person node for Andrey (with sameAs YouTube), `publisher` = {"@id":"https://nomadechosounds.com/#org"}, plus the Organization node. Copy both nodes from /recordings/mountain-river/.
  - Add the new URL to sitemap.xml with today's date as lastmod, and update the lastmod of any existing page you change.

- Pinterest: feed.xml and the pin image in /assets/pins/ are built automatically on deploy from sitemap.xml. Optionally add a line to PINS in scripts/build_feed.py with a different photo and a short key-number subtitle for the new article.
- Answer first: the first paragraph of every article starts with "<b>Short answer:</b>" and answers the page's question in 2–3 plain sentences with the key number(s). AI search engines and Google quote this paragraph, so it must make sense on its own.
- Measurement data page: whenever an article reports measurements of a recording that is not yet in /nature-sound-measurements/, add a column to its table and a row to measurements.csv (same units, "—" or empty if not measured), update "Updated <date>" and dateModified there, and its sitemap lastmod.
- Titles for "best" and comparison articles end with the current year in brackets, e.g. "(2026)". Do not add a year to other titles.

## Queue

- [x] 1. Mountain Brook — recording page with full measurements. Slug: /recordings/mountain-brook/
  - YouTube video: i1Un95nTRa0 ("Tinnitus Relief Sound Masking · Mountain Brook"). Location: Tian Shan mountains near Almaty (owner confirmed: all streams and rivers are recorded in the Tian Shan).
  - Source: mountain brook, 2026; 18 min source take (85 s excerpt analysed).
  - Loudness variation (std of level, 400 ms windows) 0.31 dB; P95–P5 spread 1.04 dB; zero frames >6 dB above median (no transients).
  - Drift across the excerpt 0.2 dB RMS; spectral centroid 1115–1136 Hz; no tonal peaks; sub-40 Hz energy 0.059%; no clipping; loop seam 0.00 dB.
  - Flaw found: left channel 3.5 dB louder than right (L/R correlation 0.58); fixed with a pan filter before looping.
  - Chain: trim spoken slate (keep 0:20–19:55), channel balance, high shelf −5 dB at 6 kHz, no compressor, peak-normalise to −3 dBFS, loop.
  - Lesson: the spot looked like a splashy cascade in photos and was almost rejected; rocks atomise the flow into even foam. Never judge by a photo; measure.
- [x] 2. Mountain River — recording page with full measurements. Slug: /recordings/mountain-river/
  - YouTube video: GM9wlcADK_s (now titled "Sleep Sounds for Insomnia · Mountain River"). Location: Tian Shan mountains near Almaty (owner confirmed: all streams and rivers are recorded in the Tian Shan).
  - Source: noisy-but-constant mountain river, 2026; 26.3 min take; spoken slate at start.
  - Core section (4–24 min): loudness variation 0.62 dB; P95–P5 2.04 dB; transients >6 dB 0.031%, >10 dB 0.000%; no tonal peaks.
  - Drift over 20 min 0.6 dB RMS; centroid 1142–1182 Hz; sub-40 Hz 0.04%; peak −6.2 dBFS, RMS −30.3 dBFS (recorded at a good level); L/R balance −0.46 dB.
  - Chain: keep 0:30–26:00, small channel-balance correction, high shelf −5 dB at 6 kHz, +2.1 dB normalisation, loop (about 18 repeats in a full night track).
- [ ] 3. How to use a masking sound at night — practical guide with an FAQ block (FAQPage structured data that matches the visible text). Slug: /how-to-use-masking-sounds-at-night/
  - Speaker vs headphones, volume (comfortable, below the tinnitus or at the blend point as audiologist sources describe), timers, consistency.
  - MUST fetch and cite 2–3 authoritative sources (audiology/clinic/national health pages). No medical advice beyond what they say.
- [ ] 4. How we record water sounds: our field setup. Slug: /how-we-record-water-sounds/ — PUBLISH ON FRIDAY 30 OCTOBER 2026.
  - Title (max 60 chars), e.g. "How We Record Water Sounds: Our Field Setup". Short answer first: Zoom H5, fur windscreen, a little back from the water (or in it, at Kapchagay), long takes on quiet weekdays.
  - Share image: /assets/share/kapchagay-zoom-h5-in-water-16x9.jpg (4x3 and 1x1 versions exist too). Add a PINS line in scripts/build_feed.py: ("kapchagay-zoom-h5-in-water", "Zoom H5 standing in the water") and a PIN_EXTRA line ("b", "gorge-stream-setup-mossy-boulders", "A recorder, a stone, a mountain stream").
  - Facts you may use (owner-confirmed, do not add others, do not invent recorder settings, gain values, mic modes or EQ numbers):
    - Audio: Zoom H5, WAV 48 kHz / 24-bit, always with a fur windscreen. Video separately on an iPhone 16 Pro in 4K. A full-size tripod with a phone holder, and a small flexible tripod.
    - Placement: recorder on a stone or on the grass a short distance back from the water, so splashes blend into one layer. At the Kapchagay reservoir (near Konaev, Almaty Region, spring 2026) the recorder stood on the flexible tripod right in the shallow water to record small waves.
    - Takes of about 20 minutes or more; a spoken slate at the start; the recordist walks away during a take so footsteps don't reach the recorder.
    - Recording level example: Mountain River peaked at -6.2 dBFS with RMS -30.3 dBFS, so the final track needed only +2.1 dB gain (link /recordings/mountain-river/).
    - Spots: weekdays, far enough from roads that engine noise disappears; even, foamy water rather than single splashes; every take is measured (link /nature-sound-measurements/).
    - Places: Big Almaty gorge at 1,466 m (autumn 2026), the Alma-Arasan gorge, the mossy pipe spring (macro setup), Kapchagay shore.
  - Photos to use (all in /assets/img, each has a .webp; width 1000 height 1500; use the .photo-pair layout from /tian-shan-field-recordings/ for pairs): kapchagay-zoom-h5-in-water, gorge-stream-setup-mossy-boulders, gorge-cliff-setup, mossy-spring-flex-tripod, mossy-pipe-setup, kapchagay-gravel-shore-setup, mossy-spring-macro-screen. Write honest alt text describing what is visible.
  - Link to /tian-shan-field-recordings/ for the full field notes. Add the Ko-fi note block as for every article.
- [ ] 5. Best natural sounds for tinnitus (2026): ranked by our own measurements. Slug: /best-natural-sounds-for-tinnitus/
  - Rank only recordings that are on /nature-sound-measurements/ (brook first, river second, birdsong last with why). Link the data page. Short answer first.
  - Cite the same research as /tinnitus-masking-sounds/ (Henry et al. 2004; Wan Mohamad et al. 2018). No medical claims beyond them.
- [ ] 6. Brook vs river vs birdsong for sleep: a measured comparison (2026). Slug: /brook-vs-river-vs-birdsong-sleep/
  - One comparison table from the data page, then which to choose when (headphones vs speaker, light vs heavy sleeper — keep this as practical listening advice, not medical advice).
- [ ] 7. Why we never use a compressor on nature recordings. Slug: /no-compressor-nature-recordings/
  - A compressor lifts the background noise and recorder hiss of natural recordings and flattens natural dynamics; we use only trim, balance, a gentle high shelf and normalisation. Use the Mountain River level figures as the example.
- [ ] 8. Stereo balance and why 3.5 dB matters in headphones over a night. Slug: /stereo-balance-sleep-sounds/
  - Use the Mountain Brook imbalance (L +3.5 dB, correlation 0.58) and the fix. Keep claims about perception general and sourced.
- [ ] 9. How we make noise colours from real water (no generated noise). Slug: /how-we-make-noise-from-real-water/
  - Facts: noise tracks are made only from the owner's recordings of streams and of water running through an abandoned steel pipe left from dam construction on a Tian Shan riverbank; shaped by equalising, filtering and taming peaks in an editor. Embed the pipe short V0CaA8UVzHE (vertical, use the .short wrapper). Do not invent EQ settings or frequencies; describe the method in general terms only.
- [ ] 10. Water vs brown noise: a measured comparison. BLOCKED — needs the owner's brown-noise file and a raw brook file to measure.
- [ ] 11. BLOCKED until the owner supplies measurements of the noise tracks: White vs pink vs brown noise vs water sounds for tinnitus (2026). Slug: /white-pink-brown-noise-vs-water-tinnitus/

## Done
- 2026-10-20: Mountain Brook recording notes — https://nomadechosounds.com/recordings/mountain-brook/
- 2026-10-23: Mountain River recording notes — https://nomadechosounds.com/recordings/mountain-river/

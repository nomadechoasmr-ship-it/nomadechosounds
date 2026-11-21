# nomadechosounds.com

Static site for Nomad Echo Sounds. Hosted on GitHub Pages. `.github/workflows/deploy.yml` deploys on every push to `main` and once a day refreshes the video library from the channel feed.

- `index.html` — home page
- `tinnitus-masking-sounds/` — tinnitus masking guide
- `assets/style.css` — shared styles
- `sitemap.xml`, `robots.txt`, `404.html`, `CNAME`
- `scripts/`, `data/`, `content-plan.md` are not published to the site

- `scripts/add_video_schema.py` runs on every deploy and adds VideoObject structured data to every page that embeds a channel video (data from `data/videos.json`). Nothing to do by hand for new articles.

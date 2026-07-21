# Porto — Personal Portfolio 2026

[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![GitHub Pages](https://img.shields.io/badge/hosted-GitHub%20Pages-blue.svg)](https://gaidajis.github.io/porto/)

> Personal portfolio website hosted on GitHub Pages.

## 🌐 Live Site

**[https://gaidajis.github.io/porto/](https://gaidajis.github.io/porto/)**

---

## 📁 Project Structure

```
porto/
├── index.html            ← Root redirect (GitHub Pages entry point)
├── extract.py            ← MHTML extraction utility (see below)
├── porto.mhtml           ← Source MHTML snapshot (Chrome save)
├── LICENSE               ← MIT License
└── porto-2026/
    ├── index.html        ← Main portfolio page
    ├── css/              ← Stylesheets (styles.css … styles5.css)
    └── images/           ← Image assets
```

---

## 🐍 extract.py — How It Works

`extract.py` is a zero-dependency Python 3 utility that unpacks a Chrome/Blink `.mhtml` file into a ready-to-deploy static site folder. It uses only the Python standard library (`email`, `pathlib`, `re`, `sys`).

### What it does, step by step

1. **Parses the MHTML archive** — An `.mhtml` file is essentially a MIME multipart email where every resource (HTML, CSS, images, fonts) is stored as a separate encoded part. The script reads the file with Python's `email.parser.BytesParser`, then walks every part using `msg.walk()`.

2. **Extracts HTML** — The first `text/html` part is written to `porto-2026/index.html`. Only the first HTML part is kept.

3. **Extracts CSS** — Each `text/css` part is saved as `css/styles.css`, `css/styles2.css`, etc. The original `Content-Location` URL and `Content-ID` header are recorded in a `url_map` dict so they can be rewritten in the HTML later.

4. **Extracts images** — Every `image/*` part is saved under `images/`. The filename is derived from the `Content-Location` header where possible (sanitised with a regex to strip unsafe characters). Collision-safe numbering prevents overwriting files with duplicate names. Both the URL and `cid:` reference are added to `url_map`.

5. **Handles other assets** — JavaScript files and web fonts (`woff`/`woff2`) are saved into `js/` and `fonts/` subdirectories respectively.

6. **Rewrites all URLs in the HTML** — After all parts are extracted, the script replaces every remote URL and `cid:` reference in `index.html` with its corresponding local relative path (e.g. `images/photo.png`, `css/styles2.css`). Keys are sorted longest-first to avoid partial-match collisions.

7. **Fixes Qwen CDN image URLs** — A secondary regex pass resolves any leftover `https://image.qwenlm.ai/...` image URLs by matching the filename against already-extracted files on disk, making the page fully self-contained and offline-ready.

### Usage

```bash
# Default: reads porto.mhtml → outputs to porto-2026/
python3 extract.py

# Custom source and output directory
python3 extract.py my-page.mhtml my-output-folder
```

### Output

The script prints a summary on completion:

```
HTML  -> porto-2026/index.html
CSS   -> porto-2026/css/styles.css
IMG   -> porto-2026/images/photo.png (84321 bytes)
...
Done. Open: /path/to/porto-2026/index.html
Images: 18  CSS parts: 5  URL rewrites: 42
```

---

## 🚀 Deployment

This site is deployed via **GitHub Pages** from the `main` branch.

The root `index.html` redirects visitors to `porto-2026/index.html`, where the full portfolio lives.

To view locally, simply open `porto-2026/index.html` in your browser — no build step required.

---

## 📄 License

This project is licensed under the [MIT License](./LICENSE).

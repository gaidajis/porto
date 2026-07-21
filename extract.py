#!/usr/bin/env python3
"""Extract HTML, CSS, and images from a Chrome/Blink .mhtml — stdlib only."""
from email import policy
from email.parser import BytesParser
from pathlib import Path
import re
import sys

def main(mhtml_path: str, out_dir: str = "porto-2026") -> None:
    mhtml = Path(mhtml_path)
    if not mhtml.is_file():
        sys.exit(f"File not found: {mhtml}")

    out = Path(out_dir)
    (out / "images").mkdir(parents=True, exist_ok=True)
    (out / "css").mkdir(exist_ok=True)

    msg = BytesParser(policy=policy.default).parsebytes(mhtml.read_bytes())

    html_path = out / "index.html"
    url_map: dict[str, str] = {}  # remote or cid -> relative local path
    img_n = 0
    css_n = 0

    for part in msg.walk():
        ctype = part.get_content_type()
        # skip multipart containers
        if ctype.startswith("multipart/"):
            continue

        payload = part.get_payload(decode=True)
        if payload is None:
            continue

        loc = (part.get("Content-Location") or "").strip()
        cid = (part.get("Content-ID") or "").strip().strip("<>")

        if ctype == "text/html":
            if not html_path.exists():
                html_path.write_bytes(payload)
                print(f"HTML  -> {html_path}")
            continue

        if ctype == "text/css":
            css_n += 1
            name = f"styles{'' if css_n == 1 else css_n}.css"
            dest = out / "css" / name
            dest.write_bytes(payload)
            rel = f"css/{name}"
            if loc:
                url_map[loc] = rel
            if cid:
                url_map[f"cid:{cid}"] = rel
                url_map[cid] = rel
            print(f"CSS   -> {dest}")
            continue

        if ctype.startswith("image/"):
            img_n += 1
            ext = {
                "image/png": ".png",
                "image/jpeg": ".jpg",
                "image/jpg": ".jpg",
                "image/webp": ".webp",
                "image/gif": ".gif",
                "image/svg+xml": ".svg",
            }.get(ctype, ".bin")

            # prefer filename from Content-Location
            base = Path(loc).name if loc else ""
            base = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
            if not base or base in (".", ".."):
                base = f"image_{img_n:03d}{ext}"
            elif not Path(base).suffix:
                base = base + ext

            dest = out / "images" / base
            # avoid overwrite collisions
            if dest.exists():
                dest = out / "images" / f"{dest.stem}_{img_n}{dest.suffix}"
            dest.write_bytes(payload)
            rel = f"images/{dest.name}"
            if loc:
                url_map[loc] = rel
            if cid:
                url_map[f"cid:{cid}"] = rel
            print(f"IMG   -> {dest} ({len(payload)} bytes)")
            continue

        # optional: fonts, js, etc.
        if ctype in ("application/javascript", "text/javascript", "font/woff2", "font/woff"):
            sub = "js" if "javascript" in ctype else "fonts"
            (out / sub).mkdir(exist_ok=True)
            name = Path(loc).name if loc else f"asset_{img_n}"
            name = re.sub(r"[^a-zA-Z0-9._-]", "_", name) or "asset"
            dest = out / sub / name
            dest.write_bytes(payload)
            if loc:
                url_map[loc] = f"{sub}/{dest.name}"
            print(f"ASSET -> {dest}")

    if not html_path.exists():
        sys.exit("No HTML part found in MHTML.")

    html = html_path.read_text(encoding="utf-8", errors="replace")

    # longest keys first so partial overlaps don't break rewrites
    for remote, local in sorted(url_map.items(), key=lambda kv: -len(kv[0])):
        if remote:
            html = html.replace(remote, local)

    # Blink often embeds cid: in stylesheet links
    html = re.sub(
        r'href="cid:[^"]+"',
        'href="css/styles.css"',
        html,
        count=1,
    )

    # rewrite leftover Qwen CDN image URLs by filename if files exist
    def qwen_repl(m: re.Match) -> str:
        fname = m.group(1)
        local = out / "images" / fname
        if local.exists():
            return f"images/{fname}"
        # try any extracted file ending with same uuid-ish name
        for p in (out / "images").glob(f"*{fname}"):
            return f"images/{p.name}"
        return m.group(0)

    html = re.sub(
        r"https://image\.qwenlm\.ai/[^\"'\s]+/([A-Za-z0-9._-]+\.(?:png|jpg|jpeg|webp|gif))",
        qwen_repl,
        html,
    )

    html_path.write_text(html, encoding="utf-8")
    print(f"\nDone. Open: {html_path.resolve()}")
    print(f"Images: {img_n}  CSS parts: {css_n}  URL rewrites: {len(url_map)}")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "Porto-2026-A-Family-Journey.mhtml"
    out = sys.argv[2] if len(sys.argv) > 2 else "porto-2026"
    main(path, out)

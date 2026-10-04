#!/usr/bin/env python3
"""Erhebt die Live-Metadaten der im Register geführten Adressen.

Redaktionell gepflegt sind Name, Kurztext, Herkunft und Farbe (targets.json).
Frisch ermittelt wird bei jedem Lauf: HTTP-Status, Antwortzeit, Beschreibung
und Vorschaubild der Zielseite. Ergebnis ist data/sites.json, die Quelle für
build.py.

Aufruf:
    python3 harvest.py                 # alles erheben
    python3 harvest.py --skip-images   # nur Status, Zeit und Texte
"""
from __future__ import annotations

import io
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).parent
TARGETS = json.loads((ROOT / "targets.json").read_text(encoding="utf-8"))["targets"]
OUT = ROOT / "data" / "sites.json"
IMG_DIR = ROOT / "assets" / "img"

UA = "projektregister-harvest/1.0 (+https://github.com/NUMEN1156/projektregister)"
TIMEOUT = 30
MAX_HTML = 2_000_000
MAX_IMAGE = 8 * 1024 * 1024
IMAGE_WIDTH = 1280
SKIP_IMAGES = "--skip-images" in sys.argv


def fetch(url: str) -> tuple[int | None, str, float]:
    """Holt eine Seite und misst die Antwortzeit. Fehler werden als Status geführt."""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de,en;q=0.7",
        },
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            body = response.read(MAX_HTML)
            charset = response.headers.get_content_charset() or "utf-8"
            return response.status, body.decode(charset, "replace"), round(time.perf_counter() - start, 2)
    except urllib.error.HTTPError as error:
        return error.code, "", round(time.perf_counter() - start, 2)
    except Exception as error:  # noqa: BLE001 - Netzfehler jeder Art wird als Ausfall geführt
        print(f"    Fehler: {type(error).__name__}: {error}", file=sys.stderr)
        return None, "", round(time.perf_counter() - start, 2)


def meta_content(markup: str, keys: tuple[str, ...]) -> str:
    """Liest den Inhalt eines Meta-Tags (property/name), Reihenfolge egal."""
    for key in keys:
        pattern = re.compile(
            r"<meta[^>]*(?:property|name)\s*=\s*[\"']" + re.escape(key) + r"[\"'][^>]*>", re.I
        )
        for tag in pattern.findall(markup):
            value = re.search(r"content\s*=\s*[\"'](.*?)[\"']", tag, re.I | re.S)
            if value:
                text = unescape(value.group(1)).strip()
                if text:
                    return text
    return ""


def page_title(markup: str) -> str:
    title = meta_content(markup, ("og:title", "twitter:title"))
    if title:
        return title
    match = re.search(r"<title[^>]*>(.*?)</title>", markup, re.I | re.S)
    return unescape(re.sub(r"\s+", " ", match.group(1))).strip() if match else ""


def clean(text: str) -> str:
    """Entfernt HTML-Reste und normalisiert Leerraum."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", unescape(text)).strip()


def save_image(url: str, target: Path) -> bool:
    """Lädt ein Vorschaubild und legt es als WebP mit fester Breite ab."""
    try:
        request = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read(MAX_IMAGE)
    except Exception as error:  # noqa: BLE001
        print(f"    Bild nicht ladbar: {type(error).__name__}", file=sys.stderr)
        return False
    try:
        from PIL import Image
    except ImportError:
        print("    Pillow fehlt (pip install pillow) - Bild übersprungen", file=sys.stderr)
        return False
    try:
        image = Image.open(io.BytesIO(raw))
        image.load()
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")
        if image.width > IMAGE_WIDTH:
            height = round(image.height * IMAGE_WIDTH / image.width)
            image = image.resize((IMAGE_WIDTH, height), Image.LANCZOS)
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(target, "WEBP", quality=82, method=6)
        return True
    except Exception as error:  # noqa: BLE001
        print(f"    Bild nicht konvertierbar: {type(error).__name__}", file=sys.stderr)
        return False


def main() -> int:
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    sites: list[dict] = []
    live = guarded = unreachable = 0

    for target in TARGETS:
        url = target["url"]
        print(f"[{target['id']}] {url}")
        status, markup, seconds = fetch(url)
        if status == 200:
            live += 1
        elif status in (401, 403):
            guarded += 1
        else:
            unreachable += 1

        description = clean(meta_content(markup, ("og:description", "description", "twitter:description")))
        name = target.get("name") or page_title(markup) or url
        tagline = target.get("tagline") or description or "Keine Beschreibung auf der Zielseite hinterlegt."

        image_path = None
        image_url = meta_content(markup, ("og:image", "twitter:image")) if status == 200 else ""
        existing = IMG_DIR / f"{target['id']:02d}.webp"
        if image_url and not SKIP_IMAGES:
            absolute = urljoin(url + "/", image_url)
            if save_image(absolute, existing):
                image_path = f"assets/img/{existing.name}"
        if image_path is None and existing.exists():
            # Vorschaubild der letzten Erhebung behalten, wenn die Seite keines mehr liefert.
            image_path = f"assets/img/{existing.name}"

        sites.append(
            {
                "id": target["id"],
                "name": name,
                "tagline": tagline,
                "url": url,
                "host": urlsplit(url).netloc,
                "origin": target.get("origin", "Web"),
                "accent": target.get("accent", "#d8b35a"),
                "status": status,
                "seconds": seconds,
                "image": image_path,
                "monogram": target.get("monogram") or "".join(p[0] for p in name.split()[:2]).upper(),
            }
        )

    payload = {
        "generated_from": "live metadata harvest",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(sites),
        "summary": {"live": live, "guarded": guarded, "unreachable": unreachable},
        "sites": sites,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n{len(sites)} Einträge geschrieben: {live} erreichbar, {guarded} geschützt, {unreachable} ohne Antwort")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

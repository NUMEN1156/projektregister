#!/usr/bin/env python3
"""Erzeugt data/playlist.json aus den Dateien in assets/audio/.

Der Player liest ausschließlich data/playlist.json. Damit genügt es, Musik
nach assets/audio/ zu legen und dieses Skript laufen zu lassen:

    python3 playlist.py && python3 build.py

ANONYME ANZEIGE: Solange ANONYMOUS auf True steht, enthält das veröffentlichte
Register keine Werknamen und keine Interpreten — nur Reihenfolge, Datei, Dauer
und Größe. Die Zuordnung der neutralen Dateinamen zu den Werktiteln landet
stattdessen in playlist-namen-privat.json, das nicht veröffentlicht wird.

Aufruf:
    python3 playlist.py               # Register erzeugen
    python3 playlist.py --mit-namen   # Namen diesmal mitschreiben (für den eigenen Gebrauch)
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
AUDIO_DIR = ROOT / "assets" / "audio"
OUT = ROOT / "data" / "playlist.json"
PRIVATE = ROOT / "playlist-namen-privat.json"
SUFFIXES = {".mp3", ".m4a", ".aac", ".ogg", ".oga", ".opus", ".wav", ".flac", ".webm"}

ANONYMOUS = "--mit-namen" not in sys.argv


def tags(path: Path) -> tuple[str, str, float | None]:
    """Liest Titel, Interpret und Dauer aus den Datei-Tags, wenn möglich."""
    title = artist = ""
    duration = None
    try:
        from mutagen import File as MutagenFile  # type: ignore

        audio = MutagenFile(path, easy=True)
        if audio is not None:
            title = (audio.get("title") or [""])[0]
            artist = (audio.get("artist") or [""])[0]
            if audio.info is not None:
                duration = float(audio.info.length)
    except Exception:  # noqa: BLE001 - ohne Tags wird der Dateiname verwendet
        pass
    return title.strip(), artist.strip(), duration


def from_filename(path: Path) -> tuple[str, str]:
    """Leitet Titel und Interpret aus dem Dateinamen ab."""
    stem = re.sub(r"[_]+", " ", path.stem).strip()
    stem = re.sub(r"\s{2,}", " ", stem)
    if " - " in stem:
        artist, title = stem.split(" - ", 1)
        return title.strip(), artist.strip()
    return stem, ""


def tidy(title: str) -> str:
    """Entfernt Dateiendungen, die aus Dateinamen in Titel gerutscht sind."""
    cleaned = re.sub(r"\.(mp4|mp3|wav|m4a|aac|ogg|opus|flac|webm)\b", "", title, flags=re.I)
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def main() -> int:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in AUDIO_DIR.rglob("*") if p.is_file() and p.suffix.lower() in SUFFIXES)

    tracks = []
    private = []
    for position, path in enumerate(files, start=1):
        title, artist, duration = tags(path)
        fallback_title, fallback_artist = from_filename(path)
        seconds = round(duration, 1) if duration else None
        private.append(
            {
                "index": position,
                "datei": path.name,
                "title": tidy(title) or fallback_title,
                "artist": tidy(artist) or fallback_artist,
                "seconds": seconds,
            }
        )
        entry = {
            "index": position,
            "label": f"Titel {position:02d}",
            "src": path.relative_to(ROOT).as_posix(),
            "duration": seconds,
            "bytes": path.stat().st_size,
        }
        if not ANONYMOUS:
            entry["title"] = private[-1]["title"]
            entry["artist"] = private[-1]["artist"]
        tracks.append(entry)

    total = round(sum(t["duration"] or 0 for t in tracks), 1)
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(tracks),
        "total_seconds": total,
        "anonymous": ANONYMOUS,
        "note": (
            "Musik des Projektregisters. Dateien liegen in assets/audio/; dieses Register wird "
            "mit 'python3 playlist.py' neu erzeugt und von build.py in die Seite eingebettet. "
            + ("Die Anzeige erfolgt ohne Werknamen." if ANONYMOUS else "Werknamen sind enthalten.")
        ),
        "tracks": tracks,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PRIVATE.write_text(
        json.dumps(
            {
                "note": "Zuordnung der Dateien zu den Werknamen. Nur für den eigenen Gebrauch; nicht veröffentlichen.",
                "tracks": private,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    if tracks:
        mode = "ohne Werknamen" if ANONYMOUS else "mit Werknamen"
        print(f"{len(tracks)} Titel eingetragen ({total / 60:.1f} Minuten, Anzeige {mode}):")
        for entry in tracks:
            mark = entry.get("title", "—")
            print(f"  {entry['label']}  {entry['src']}  {duration_text(entry['duration'])}  {mark if not ANONYMOUS else ''}".rstrip())
        print(f"Zuordnung gesichert in {PRIVATE.name}")
    else:
        print("Keine Audiodateien in assets/audio/ gefunden - Register bleibt leer.")
    return 0


def duration_text(seconds: float | None) -> str:
    if not seconds:
        return "—:—"
    return f"{int(seconds // 60)}:{int(seconds % 60):02d}"


if __name__ == "__main__":
    sys.exit(main())
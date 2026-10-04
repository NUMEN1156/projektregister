#!/usr/bin/env python3
"""Erzeugt index.html aus data/sites.json.

Die Karten werden statisch ausgeliefert (lesbar ohne JavaScript, sichtbar für
Crawler und Agenten); assets/app.js blendet beim Filtern nur ein und aus.
"""
from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / "data/sites.json").read_text(encoding="utf-8"))
SITES = DATA["sites"]

PLAYLIST_PATH = ROOT / "data" / "playlist.json"
PLAYLIST = json.loads(PLAYLIST_PATH.read_text(encoding="utf-8")) if PLAYLIST_PATH.exists() else {"tracks": []}
TRACKS = PLAYLIST.get("tracks", [])
# Als JSON in die Seite eingebettet; "<" wird maskiert, damit das Skript-Tag sicher bleibt.
PLAYLIST_JSON = json.dumps({"tracks": TRACKS}, ensure_ascii=False).replace("<", "\\u003c")

ORIGINS = [("alle", "Alle"), ("manus.space", "Manus"), ("lovable.app", "Lovable"),
           ("agentui.app", "AgentUI"), ("live", "Erreichbar"), ("geschaetzt", "Geschützt")]


def esc(value: str) -> str:
    return html.escape(value or "", quote=True)


def status_tag(status: int | None, seconds: float | None) -> tuple[str, str]:
    if status == 200:
        return "tag--live", f"live · {seconds:.1f}s" if seconds else "live"
    if status in (401, 403):
        return "tag--guarded", f"geschützt · {status}"
    return "", f"Status {status}" if status else "unbekannt"


def card(site: dict, index: int) -> str:
    cls, label = status_tag(site.get("status"), site.get("seconds"))
    media = (
        f'<img src="{esc(site["image"])}" alt="Vorschau: {esc(site["name"])}" loading="lazy" decoding="async">'
        if site.get("image")
        else f'<div class="card__monogram" aria-hidden="true">{esc(site["monogram"])}</div>'
    )
    return f"""      <article class="card" data-origin="{esc(site['host'])}" data-status="{site.get('status') or ''}"
               style="--accent: {esc(site['accent'])}; --delay: {index * 55}ms">
        <a class="card__link" href="{esc(site['url'])}" target="_blank" rel="noopener"
           aria-label="{esc(site['name'])} öffnen"></a>
        <div class="card__media">
          {media}
          <div class="card__badge">
            <span class="tag">{esc(site['origin'])}</span>
            <span class="tag {cls}">{esc(label)}</span>
          </div>
        </div>
        <div class="card__body">
          <h3 class="card__name">{esc(site['name'])}</h3>
          <p class="card__tagline">{esc(site['tagline'])}</p>
          <div class="card__meta">
            <span>{esc(site['host'])}</span>
            <span class="card__open">öffnen ↗</span>
          </div>
        </div>
      </article>"""


live = sum(1 for s in SITES if s.get("status") == 200)
guarded = sum(1 for s in SITES if s.get("status") in (401, 403))
stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
track_state = "ready" if TRACKS else "empty"
track_initial_title = (
    TRACKS[0].get("title") or TRACKS[0].get("label") or "Titel 01"
) if TRACKS else "Noch keine Titel hinterlegt"
track_initial_cover = (TRACKS[0].get("cover") or "") if TRACKS else ""
track_initial_artist = (
    f"{len(TRACKS)} Titel · {PLAYLIST.get('total_seconds', 0) / 60:.0f} Minuten"
    if TRACKS
    else "Dateien nach assets/audio/ legen, dann python3 playlist.py"
)
chips = "\n".join(
    f'          <button class="chip" type="button" data-filter="{key}" aria-pressed="{"true" if key == "alle" else "false"}">{label}</button>'
    for key, label in ORIGINS
)
cards = "\n".join(card(s, i) for i, s in enumerate(SITES))

page = f"""<!doctype html>
<html lang="de">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Projektregister — {len(SITES)} laufende Instanzen</title>
    <meta name="description" content="Übersicht der laufenden Web-Projekte: Titel, Kurzbeschreibung, Herkunft, Erreichbarkeit und Direktlink — erzeugt aus den Metadaten der Seiten selbst.">
    <meta name="color-scheme" content="dark">
    <meta name="theme-color" content="#08090c">
    <link rel="stylesheet" href="assets/styles.css">
    <link rel="alternate" type="application/json" href="data/sites.json" title="Maschinenlesbares Register">
    <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%2308090c'/%3E%3Cpath d='M8 22V10h4.5l3.5 7 3.5-7H24v12h-3.2v-6.6L17.6 22h-3.2l-3.2-6.6V22z' fill='%23d8b35a'/%3E%3C/svg%3E">
  </head>
  <body>
    <header class="masthead">
      <div class="wrap masthead__inner">
        <div class="wordmark">
          <span class="wordmark__mark">Register</span>
          <span class="wordmark__name">Projektübersicht</span>
        </div>
        <div class="masthead__meta">
          <span>Stand <b>{esc(stamp)}</b></span>
          <span>Instanzen <b>{len(SITES)}</b></span>
          <span>Erreichbar <b>{live}</b></span>
        </div>
      </div>
    </header>

    <main class="wrap">
      <section class="lede">
        <p class="lede__eyebrow">Laufende Instanzen</p>
        <h1>Alles, was gerade online ist — an einem Ort.</h1>
        <p>Titel, Kurzbeschreibung, Herkunft und Erreichbarkeit stammen aus den Metadaten der
           Seiten selbst, nicht aus einer gepflegten Liste. Grundlage ist eine Erhebung vom
           {esc(stamp)}.</p>
        <div class="lede__facts">
          <div class="fact"><div class="fact__value">{len(SITES)}</div><div class="fact__label">Instanzen</div></div>
          <div class="fact"><div class="fact__value">{live}</div><div class="fact__label">antworten mit 200</div></div>
          <div class="fact"><div class="fact__value">{guarded}</div><div class="fact__label">hinter Zugangsschutz</div></div>
          <div class="fact"><div class="fact__value">3</div><div class="fact__label">Plattformen</div></div>
        </div>
      </section>

      <section class="controls" aria-label="Filter">
        <span class="controls__label">Filter</span>
{chips}
        <span class="controls__label" style="margin-left:auto">angezeigt <b data-visible-count {""}>{len(SITES)}</b></span>
      </section>

      <section class="grid" aria-label="Projekte">
{cards}
      </section>

      <section class="agents">
        <h2>Für Agenten und Werkzeuge</h2>
        <p>Dieselben Daten liegen strukturiert daneben und sind direkt abrufbar — ohne HTML-Auswertung.</p>
        <p><code>data/sites.json</code> — Felder je Eintrag: <code>id</code>, <code>name</code>,
           <code>tagline</code>, <code>url</code>, <code>host</code>, <code>origin</code>,
           <code>status</code>, <code>seconds</code>, <code>image</code>, <code>monogram</code>.</p>
        <p>Neu erzeugen: <code>python3 build.py</code> (liest <code>data/sites.json</code>).</p>
        <p><code>data/playlist.json</code> — Titel des Musikplayers: <code>title</code>, <code>artist</code>,
           <code>src</code>, <code>duration</code>, <code>bytes</code>. Neu erzeugen: <code>python3 playlist.py</code>.</p>
      </section>

      <footer class="foot">
        <span>Projektregister · erzeugt aus Live-Metadaten</span>
        <span>{len(SITES)} Einträge · {esc(stamp)}</span>
      </footer>
    </main>

    <section class="player" id="player" data-state="{track_state}" aria-label="Musikplayer">
      <audio id="audio" preload="metadata"></audio>
      <div class="wrap player__inner">
        <div class="player__now">
          <span class="player__cover" id="track-cover-frame" data-state="{('ready' if track_initial_cover else 'none')}">
            <img id="track-cover" alt="" loading="lazy"{(' src="' + esc(track_initial_cover) + '"') if track_initial_cover else ''}>
          </span>
          <span class="player__eyebrow">Klangbett</span>
          <span class="player__title" id="track-title">{esc(track_initial_title)}</span>
          <span class="player__artist" id="track-artist">{esc(track_initial_artist)}</span>
        </div>
        <div class="player__transport">
          <button type="button" class="pbtn" data-action="prev" aria-label="Vorheriger Titel">◀◀</button>
          <button type="button" class="pbtn pbtn--main" data-action="toggle" aria-label="Wiedergabe starten">▶</button>
          <button type="button" class="pbtn" data-action="next" aria-label="Nächster Titel">▶▶</button>
        </div>
        <div class="player__timeline">
          <span class="player__time" id="time-current">0:00</span>
          <input class="player__seek" type="range" id="seek" min="0" max="1000" value="0" step="1"
                 aria-label="Position im Titel">
          <span class="player__time" id="time-total">0:00</span>
        </div>
        <div class="player__volume">
          <input class="player__vol" type="range" id="volume" min="0" max="100" value="70" step="1"
                 aria-label="Lautstärke">
          <button type="button" class="pbtn pbtn--list" data-action="list" aria-expanded="false"
                  aria-controls="playlist">Titel <b id="track-count">{len(TRACKS)}</b></button>
        </div>
      </div>
      <ol class="playlist" id="playlist" hidden></ol>
    </section>
    <script type="application/json" id="playlist-data">{PLAYLIST_JSON}</script>

    <script src="assets/app.js" defer></script>
    <script src="assets/player.js" defer></script>
  </body>
</html>
"""

(ROOT / "index.html").write_text(page, encoding="utf-8")
print(f"index.html geschrieben: {len(SITES)} Karten, {live} erreichbar, {guarded} geschützt")

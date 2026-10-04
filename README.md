# Projektregister

Statische Übersichtsseite der laufenden Web-Instanzen: Titel, Kurzbeschreibung, Herkunft,
Erreichbarkeit und Direktlink je Projekt — dazu ein Musikplayer für die eigenen Töne.

Die Angaben stammen **aus den Seiten selbst** (Titel, `description`/`og:description`,
`og:image`, HTTP-Status und Antwortzeit einer Erhebung). Redaktionell gepflegt sind nur Name,
Kurztext, Herkunft und Farbe in `targets.json`. Fehlt eine Beschreibung auf der Zielseite,
steht das dort ausdrücklich so.

## Aufbau

| Pfad | Inhalt |
| --- | --- |
| `index.html` | Fertige Seite; Karten und Player stehen statisch im HTML (lesbar ohne JavaScript) |
| `assets/styles.css` | Design-System (dunkler Grund, goldene Signaturfarbe, Monospace-Beschriftungen, Raster) |
| `assets/app.js` | Filterlogik; blendet vorhandene Karten ein und aus |
| `assets/player.js` | Musikplayer: Wiedergabe, Titelliste, Tastenkürzel |
| `assets/img/*.webp` | Vorschaubilder, auf 1280 px Breite normalisiert |
| `assets/audio/` | Tondateien des Players |
| `targets.json` | Gepflegte Ziele (Adresse, Name, Kurztext, Herkunft, Farbe) |
| `harvest.py` | Erhebt Status, Antwortzeit, Beschreibung und Vorschaubild der Ziele |
| `playlist.py` | Liest die Tondateien und schreibt `data/playlist.json` |
| `data/sites.json` | Maschinenlesbares Register — Quelle für den Generator |
| `data/playlist.json` | Titelregister — Quelle für den Player |
| `build.py` | Erzeugt `index.html` aus beiden Registern |
| `.github/workflows/refresh.yml` | Takt: erhebt und veröffentlicht automatisch |

## Felder je Eintrag

`id`, `name`, `tagline`, `url`, `host`, `origin`, `accent`, `status`, `seconds`, `image`,
`monogram`. `status` ist der beobachtete HTTP-Code (`200` erreichbar, `401`/`403` hinter
Zugangsschutz); `seconds` die gemessene Antwortzeit.

## Neu erzeugen

```sh
python3 harvest.py     # Live-Werte erheben  → data/sites.json
python3 playlist.py    # Tondateien einlesen → data/playlist.json
python3 build.py       # beides einbetten    → index.html
```

`harvest.py --skip-images` erhebt nur Status, Zeit und Texte. Ziele ändern:
`targets.json` bearbeiten, dann erneut erheben.

## Automatischer Takt

`.github/workflows/refresh.yml` läuft **täglich 05:17 UTC**, zusätzlich von Hand
(`workflow_dispatch`) und bei jeder Änderung an `targets.json`, `harvest.py` oder `build.py`.
Der Lauf erhebt die Live-Werte, erzeugt die Seite neu und schreibt das Ergebnis zurück auf
`main` — nur wenn sich etwas geändert hat. Der eingebaute `GITHUB_TOKEN` genügt dafür.

## Betrieb

Reine statische Dateien — jeder Webserver genügt. Lokal:

```sh
python3 -m http.server 4100
```

## Grenzen

Erreichbarkeit und Antwortzeit sind Momentaufnahmen der letzten Erhebung, keine
Verfügbarkeitsüberwachung. Hinter Zugangsschutz liegende Seiten zeigen keine Vorschau. Die
Bilder sind Vorschaubilder der jeweiligen Herkunft. Der Player startet nur auf Klick —
Browser erlauben kein automatisches Abspielen mit Ton.
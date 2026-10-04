# Projektregister

Statische Übersichtsseite der laufenden Web-Instanzen: Titel, Kurzbeschreibung, Herkunft,
Erreichbarkeit und Direktlink je Projekt.

Die Angaben stammen **aus den Seiten selbst** (Titel, `description`/`og:description`,
`og:image`, HTTP-Status und Antwortzeit einer Erhebung), nicht aus einer gepflegten Liste.
Fehlt eine Beschreibung auf der Zielseite, steht das dort ausdrücklich so.

## Aufbau

| Pfad | Inhalt |
| --- | --- |
| `index.html` | Fertige Seite; Karten stehen statisch im HTML (lesbar ohne JavaScript, sichtbar für Crawler) |
| `assets/styles.css` | Design-System (dunkler Grund, goldene Signaturfarbe, Monospace-Beschriftungen, Raster) |
| `assets/app.js` | Nur Filterlogik; blendet vorhandene Karten ein und aus |
| `data/sites.json` | Maschinenlesbares Register — die Quelle für den Generator |
| `assets/img/*.webp` | Vorschaubilder, auf 1280 px Breite normalisiert |
| `build.py` | Erzeugt `index.html` aus `data/sites.json` |

## Felder je Eintrag

`id`, `name`, `tagline`, `url`, `host`, `origin`, `accent`, `status`, `seconds`, `image`,
`monogram`. `status` ist der beobachtete HTTP-Code (`200` erreichbar, `401`/`403` hinter
Zugangsschutz); `seconds` die gemessene Antwortzeit.

## Neu erzeugen

```sh
python3 build.py       # liest data/sites.json, schreibt index.html
```

Zum Aktualisieren mit frischen Werten: Metadaten der Ziele erneut erheben, `data/sites.json`
anpassen, `build.py` laufen lassen. Bilder gehören nach `assets/img/`.

## Betrieb

Reine statische Dateien — jeder Webserver genügt. Lokal:

```sh
python3 -m http.server 4100
```

## Grenzen

Erreichbarkeit und Antwortzeit sind Momentaufnahmen der letzten Erhebung, keine
Verfügbarkeitsüberwachung. Hinter Zugangsschutz liegende Seiten zeigen keine Vorschau. Die
Bilder sind Vorschaubilder der jeweiligen Herkunft.
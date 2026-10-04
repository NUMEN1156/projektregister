# Musik

Hier liegen die Tondateien des Players.

**Einen Titel hinzufügen**

1. Datei in diesen Ordner legen — unterstützt werden `.mp3`, `.m4a`, `.aac`,
   `.ogg`, `.opus`, `.wav`, `.flac`, `.webm`.
2. `python3 playlist.py` — liest Titel, Interpret und Dauer (Datei-Tags, sonst
   der Dateiname) und schreibt `data/playlist.json`.
3. `python3 build.py` — bettet das Register in `index.html` ein.

**Namensregel:** `Interpret - Titel.mp3` trennt Interpret und Titel; ohne
Bindestrich gilt der Dateiname als Titel. Umlaute und Leerzeichen sind erlaubt.

**Hinweise:** Große Dateien besser als `.m4a` oder `.mp3` mit 128–192 kbit/s
ablegen — GitHub Pages begrenzt einzelne Dateien auf 100 MB und Repositorys
auf 1 GB. Die Wiedergabe startet erst auf Klick; Browser erlauben kein
automatisches Abspielen mit Ton.
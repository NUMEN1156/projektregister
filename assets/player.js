/* Musikplayer des Projektregisters.
 *
 * Aufgaben: Titel wählen, abspielen, springen, Lautstärke regeln, Titelliste
 * ein- und ausklappen. Die Titel stammen aus data/playlist.json (Feld tracks)
 * und werden beim Erzeugen der Seite mitgeliefert — der Player braucht dafür
 * keinen zusätzlichen Abruf.
 *
 * Anzeige ohne Werknamen: Enthält das Register keine Titel, zeigt der Player
 * neutrale Beschriftungen ("Titel 01"), wie es die anonyme Ausgabe von
 * playlist.py vorsieht.
 *
 * Tastenkürzel (außerhalb von Eingabefeldern):
 *   Leertaste  Wiedergabe/Pause      ← / →  5 Sekunden zurück/vor
 *   ↑ / ↓      lauter/leiser         N / P   nächster/vorheriger Titel
 *
 * Ohne hinterlegte Titel bleibt die Leiste sichtbar, aber untätig; die
 * Beschriftung nennt dann den Ablageort für Dateien.
 */
(() => {
  const panel = document.getElementById('player')
  if (!panel) return

  const audio = document.getElementById('audio')
  const list = document.getElementById('playlist')
  const dataEl = document.getElementById('playlist-data')
  const titleEl = document.getElementById('track-title')
  const artistEl = document.getElementById('track-artist')
  const seek = document.getElementById('seek')
  const volume = document.getElementById('volume')
  const timeCurrent = document.getElementById('time-current')
  const timeTotal = document.getElementById('time-total')
  const countEl = document.getElementById('track-count')
  const coverEl = document.getElementById('track-cover')
  const coverFrame = document.getElementById('track-cover-frame')
  const toggleBtn = panel.querySelector('[data-action="toggle"]')
  const listBtn = panel.querySelector('[data-action="list"]')

  let tracks = []
  try {
    tracks = JSON.parse(dataEl.textContent || '{}').tracks || []
  } catch (error) {
    tracks = []
  }

  countEl.textContent = String(tracks.length)

  const format = (seconds) => {
    if (!Number.isFinite(seconds) || seconds < 0) return '0:00'
    const minutes = Math.floor(seconds / 60)
    const rest = Math.floor(seconds % 60)
    return minutes + ':' + String(rest).padStart(2, '0')
  }

  if (tracks.length === 0) {
    panel.dataset.state = 'empty'
    titleEl.textContent = 'Noch keine Titel hinterlegt'
    artistEl.textContent = 'Dateien nach assets/audio/ legen, dann "python3 playlist.py && python3 build.py"'
    toggleBtn.disabled = true
    panel.querySelector('[data-action="prev"]').disabled = true
    panel.querySelector('[data-action="next"]').disabled = true
    seek.disabled = true
    return
  }

  const store = {
    key: 'projektregister:player',
    read() {
      try {
        return JSON.parse(localStorage.getItem(this.key) || '{}')
      } catch (error) {
        return {}
      }
    },
    write(patch) {
      try {
        localStorage.setItem(this.key, JSON.stringify({ ...this.read(), ...patch }))
      } catch (error) {
        /* Speichern ist Kür, nicht Pflicht. */
      }
    },
  }

  const saved = store.read()
  let index = Number.isInteger(saved.index) && saved.index < tracks.length ? saved.index : 0

  // Neutrale Beschriftung: Werkname, falls vorhanden, sonst "Titel NN".
  const label = (position) =>
    tracks[position].title || tracks[position].label || 'Titel ' + String(position + 1).padStart(2, '0')

  const render = () => {
    const track = tracks[index]
    titleEl.textContent = label(index)
    artistEl.textContent = track.artist || (tracks.length + ' Titel · Klangbett')
    if (coverEl && coverFrame) {
      if (track.cover) {
        if (coverEl.getAttribute('src') !== track.cover) coverEl.setAttribute('src', track.cover)
        coverFrame.dataset.state = 'ready'
      } else {
        coverFrame.dataset.state = 'none'
      }
    }
    panel.dataset.state = audio.paused ? 'paused' : 'playing'
    toggleBtn.textContent = audio.paused ? '▶' : '❚❚'
    toggleBtn.setAttribute('aria-label', audio.paused ? 'Wiedergabe starten' : 'Wiedergabe anhalten')
    list.querySelectorAll('li').forEach((item, position) => {
      item.classList.toggle('is-active', position === index)
    })
    document.title = audio.paused ? 'Projektregister — laufende Instanzen' : '▶ Projektregister — Wiedergabe'
  }

  const load = (position, play = false) => {
    index = (position + tracks.length) % tracks.length
    const track = tracks[index]
    audio.src = track.src
    store.write({ index })
    if (play) {
      audio.play().catch(() => render())
    }
    render()
    if ('mediaSession' in navigator) {
      const meta = {
        title: label(index),
        artist: 'Projektregister',
        album: 'Projektregister',
      }
      if (track.cover) {
        meta.artwork = [
          {
            src: new URL(track.cover, document.baseURI).href,
            sizes: '720x720',
            type: 'image/webp',
          },
        ]
      }
      navigator.mediaSession.metadata = new window.MediaMetadata(meta)
    }
  }

  tracks.forEach((track, position) => {
    const item = document.createElement('li')
    const button = document.createElement('button')
    button.type = 'button'
    button.innerHTML = (track.cover ? '<img class="playlist__cover" src="' + track.cover + '" alt="" loading="lazy">' : '')
      + '<span class="playlist__pos">' + String(position + 1).padStart(2, '0') + '</span>'
      + '<span class="playlist__title">' + label(position) + '</span>'
      + '<span class="playlist__time">' + (track.duration ? format(track.duration) : '—') + '</span>'
    button.addEventListener('click', () => load(position, true))
    item.appendChild(button)
    list.appendChild(item)
  })

  const step = (delta) => {
    if (!audio.duration) return
    audio.currentTime = Math.min(audio.duration, Math.max(0, audio.currentTime + delta))
  }

  panel.addEventListener('click', (event) => {
    const action = event.target.closest('[data-action]')?.dataset.action
    if (action === 'toggle') {
      audio.paused ? audio.play().catch(() => {}) : audio.pause()
    } else if (action === 'next') {
      load(index + 1, !audio.paused)
    } else if (action === 'prev') {
      audio.currentTime > 3 ? (audio.currentTime = 0) : load(index - 1, !audio.paused)
    } else if (action === 'list') {
      const open = list.hidden
      list.hidden = !open
      listBtn.setAttribute('aria-expanded', String(open))
    }
  })

  seek.addEventListener('input', () => {
    if (audio.duration) audio.currentTime = (Number(seek.value) / 1000) * audio.duration
  })
  volume.addEventListener('input', () => {
    audio.volume = Number(volume.value) / 100
    store.write({ volume: Number(volume.value) })
  })

  audio.addEventListener('timeupdate', () => {
    timeCurrent.textContent = format(audio.currentTime)
    if (audio.duration) seek.value = String(Math.round((audio.currentTime / audio.duration) * 1000))
  })
  audio.addEventListener('loadedmetadata', () => {
    timeTotal.textContent = format(audio.duration)
  })
  audio.addEventListener('ended', () => load(index + 1, true))
  audio.addEventListener('play', render)
  audio.addEventListener('pause', render)

  document.addEventListener('keydown', (event) => {
    const target = event.target
    if (target instanceof HTMLElement
      && (target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT', 'BUTTON'].includes(target.tagName))) return
    if (event.code === 'Space') {
      event.preventDefault()
      audio.paused ? audio.play().catch(() => {}) : audio.pause()
    } else if (event.key === 'ArrowRight') {
      step(5)
    } else if (event.key === 'ArrowLeft') {
      step(-5)
    } else if (event.key === 'ArrowUp') {
      volume.value = String(Math.min(100, Number(volume.value) + 5))
      volume.dispatchEvent(new Event('input'))
    } else if (event.key === 'ArrowDown') {
      volume.value = String(Math.max(0, Number(volume.value) - 5))
      volume.dispatchEvent(new Event('input'))
    } else if (event.key.toLowerCase() === 'n') {
      load(index + 1, !audio.paused)
    } else if (event.key.toLowerCase() === 'p') {
      load(index - 1, !audio.paused)
    }
  })

  if ('mediaSession' in navigator) {
    navigator.mediaSession.setActionHandler('play', () => audio.play().catch(() => {}))
    navigator.mediaSession.setActionHandler('pause', () => audio.pause())
    navigator.mediaSession.setActionHandler('nexttrack', () => load(index + 1, true))
    navigator.mediaSession.setActionHandler('previoustrack', () => load(index - 1, true))
  }

  const initialVolume = Number.isFinite(saved.volume) ? saved.volume : 70
  volume.value = String(initialVolume)
  audio.volume = initialVolume / 100
  load(index, false)
})();

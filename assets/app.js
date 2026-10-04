/* Filter für das Projektregister.
   Die Karten stehen bereits im HTML (auch ohne JavaScript lesbar);
   dieses Skript blendet nur ein und aus. */

(function () {
  'use strict'

  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip[data-filter]'))
  var cards = Array.prototype.slice.call(document.querySelectorAll('.card[data-origin]'))
  var counter = document.querySelector('[data-visible-count]')
  var active = 'alle'

  function apply() {
    var visible = 0
    cards.forEach(function (card) {
      var origin = card.getAttribute('data-origin')
      var status = card.getAttribute('data-status')
      var show =
        (active === 'alle') ||
        (active === origin) ||
        (active === 'geschaetzt' && status !== '200') ||
        (active === 'live' && status === '200')
      card.classList.toggle('is-hidden', !show)
      if (show) visible += 1
    })
    if (counter) counter.textContent = String(visible)
  }

  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      active = chip.getAttribute('data-filter')
      chips.forEach(function (other) {
        other.setAttribute('aria-pressed', other === chip ? 'true' : 'false')
      })
      apply()
    })
  })

  apply()
})()
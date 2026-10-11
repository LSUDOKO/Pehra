/* Pehra landing page: menu, scroll reveals, count-up, the stories rail. No scroll listeners. */
(function () {
  'use strict';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var toggle = document.querySelector('.menu-toggle');
  var links = document.querySelector('.nav-links');
  toggle.addEventListener('click', function () {
    var open = !links.classList.contains('open');
    links.classList.toggle('open', open);
    toggle.setAttribute('aria-expanded', String(open));
  });
  links.addEventListener('click', function (e) { if (e.target.closest('a')) { links.classList.remove('open'); toggle.setAttribute('aria-expanded', 'false'); } });

  function countUp(el) {
    var target = Number(el.getAttribute('data-count'));
    if (!target || reduce) return;
    var text = el.textContent, start = performance.now(), dur = 1400;
    function tick(now) {
      var k = Math.min(1, (now - start) / dur), e = 1 - Math.pow(1 - k, 3);
      el.textContent = Math.round(target * e).toLocaleString('en-IN');
      if (k < 1) requestAnimationFrame(tick); else el.textContent = text;
    }
    requestAnimationFrame(tick);
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (!en.isIntersecting) return;
      en.target.classList.add('in');
      var n = en.target.querySelector('[data-count]');
      if (n) countUp(n);
      io.unobserve(en.target);
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -5% 0px' });
  setTimeout(function () { document.querySelectorAll('.reveal:not(.in)').forEach(function (el) { el.classList.add('in'); }); }, 4000);
  document.querySelectorAll('.reveal').forEach(function (el) { io.observe(el); });

  var rail = document.querySelector('.rail');
  document.querySelectorAll('.rail-btn').forEach(function (b) {
    b.addEventListener('click', function () {
      var card = rail.querySelector('.story');
      rail.scrollBy({ left: Number(b.getAttribute('data-dir')) * (card.offsetWidth + 24), behavior: reduce ? 'auto' : 'smooth' });
    });
  });

  // Videos live in S3 behind a redirect: only fetch once they are near the viewport.
  var vio = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (!en.isIntersecting) return;
      var v = en.target;
      v.preload = 'metadata';
      if (v.autoplay) { v.load(); v.play().catch(function () {}); }
      vio.unobserve(v);
    });
  }, { rootMargin: '200px' });
  document.querySelectorAll('video').forEach(function (v) { vio.observe(v); });
})();

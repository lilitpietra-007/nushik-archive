/* Runtime for the static site: language, reveal-on-scroll, and the zoom viewer.
   No router here - every collection is a real page at its own URL, so images
   load per page and the browser caches them between visits. */
(function () {
  var root = document.documentElement;

  /* ---------- language ---------- */
  var btns = Array.prototype.slice.call(document.querySelectorAll('.lang-btn'));
  function setLang(l) {
    root.setAttribute('data-lang', l);
    root.setAttribute('lang', l);
    btns.forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.getAttribute('data-set') === l));
    });
    try { localStorage.setItem('nm-lang', l); } catch (e) {}
    if (typeof window.nmRelabel === 'function') window.nmRelabel();
    var t = document.querySelector('title[data-' + l + ']');
    if (t) document.title = t.getAttribute('data-' + l);
  }
  var stored = null;
  try { stored = localStorage.getItem('nm-lang'); } catch (e) {}
  var nl = (navigator.language || '').toLowerCase();
  setLang(stored || (nl.indexOf('hy') === 0 ? 'hy' : 'en'));
  btns.forEach(function (b) {
    b.addEventListener('click', function () { setLang(b.getAttribute('data-set')); });
  });

  /* ---------- reveal on scroll ---------- */
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var items = document.querySelectorAll('.reveal');
  if (reduce || !('IntersectionObserver' in window)) {
    Array.prototype.forEach.call(items, function (el) { el.classList.add('is-visible'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry, i) {
        if (entry.isIntersecting) {
          var el = entry.target;
          setTimeout(function () { el.classList.add('is-visible'); }, (i % 3) * 100);
          io.unobserve(el);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    Array.prototype.forEach.call(items, function (el) { io.observe(el); });
  }

  /* ---------- zoom viewer ---------- */
  var lb = document.getElementById('lb');
  if (!lb) return;
  var stage = lb.querySelector('.lb-stage'), img = lb.querySelector('.lb-img');
  var cap = lb.querySelector('.lb-cap'), pct = lb.querySelector('.lb-pct');
  var figs = [], index = 0, lastFocus = null, scale = 1, tx = 0, ty = 0, base = null;
  var MIN = 1, MAX = 6;
  var L = {
    en: {close:'Close', zin:'Zoom in', zout:'Zoom out', prev:'Previous piece',
         next:'Next piece', reset:'Reset zoom', open:'Open larger to see the stitching'},
    hy: {close:'Փակել', zin:'Խոշորացնել', zout:'Փոքրացնել', prev:'Նախորդ գործը',
         next:'Հաջորդ գործը', reset:'Վերականգնել', open:'Բացել մեծացված'}
  };
  function lang(){ return root.getAttribute('data-lang') === 'hy' ? 'hy' : 'en'; }
  function labels(){
    var t = L[lang()];
    lb.querySelector('.lb-close').setAttribute('aria-label', t.close);
    lb.querySelector('[data-act="in"]').setAttribute('aria-label', t.zin);
    lb.querySelector('[data-act="out"]').setAttribute('aria-label', t.zout);
    lb.querySelector('[data-act="reset"]').setAttribute('aria-label', t.reset);
    lb.querySelector('[data-act="prev"]').setAttribute('aria-label', t.prev);
    lb.querySelector('[data-act="next"]').setAttribute('aria-label', t.next);
    document.querySelectorAll('.plate,.work').forEach(function (f) {
      var b = f.querySelector('.plate-open,.work-open'), h = f.querySelector('h3.i18n.' + lang());
      if (b && h) b.setAttribute('aria-label', h.textContent.trim() + ' — ' + t.open);
    });
  }
  window.nmRelabel = labels;
  function apply(){ img.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + scale + ')'; }
  function measure(){ img.style.transform = 'none'; var r = img.getBoundingClientRect(); base = {w:r.width, h:r.height}; apply(); }
  function clampPan(){
    if (!base) return;
    var mx = Math.max(0, (base.w*scale - stage.clientWidth)/2), my = Math.max(0, (base.h*scale - stage.clientHeight)/2);
    tx = Math.min(mx, Math.max(-mx, tx)); ty = Math.min(my, Math.max(-my, ty));
  }
  function setScale(s, cx, cy){
    var prev = scale; scale = Math.min(MAX, Math.max(MIN, s));
    if (cx != null && scale !== prev){ var k = scale/prev; tx = cx - k*(cx-tx); ty = cy - k*(cy-ty); }
    if (scale === MIN){ tx = 0; ty = 0; }
    clampPan(); apply(); pct.textContent = Math.round(scale*100) + '%';
  }
  function stageXY(e){ var r = stage.getBoundingClientRect(); return {x: e.clientX-(r.left+r.width/2), y: e.clientY-(r.top+r.height/2)}; }
  function show(i){
    index = (i + figs.length) % figs.length;
    var f = figs[index], b = f.querySelector('.plate-open,.work-open,.hang-open'), l = lang();
    var num = f.querySelector('.num .i18n.' + l);
    var ttl = f.querySelector('h3.i18n.' + l) || f.querySelector('.hang-title.i18n.' + l);
    img.src = b.getAttribute('data-zoom') || '';
    var pic = f.querySelector('img'); img.alt = pic ? (pic.getAttribute('alt') || '') : '';
    cap.setAttribute('lang', l);
    cap.innerHTML = '';
    cap.appendChild(document.createTextNode(ttl ? ttl.textContent.trim() : ''));
    if (num){ var sp = document.createElement('span'); sp.textContent = num.textContent.trim(); cap.appendChild(sp); }
    scale = 1; tx = 0; ty = 0;
    if (img.complete) measure(); else img.addEventListener('load', measure, {once:true});
    setScale(1);
  }
  function open(list, i, trigger){
    figs = list; lastFocus = trigger || document.activeElement;
    lb.setAttribute('open',''); lb.setAttribute('aria-hidden','false');
    document.body.style.overflow = 'hidden'; labels(); show(i);
    lb.querySelector('.lb-close').focus();
  }
  function close(){
    lb.removeAttribute('open'); lb.setAttribute('aria-hidden','true');
    document.body.style.overflow = ''; img.removeAttribute('src');
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  document.addEventListener('click', function (e) {
    var btn = e.target.closest && e.target.closest('.plate-open,.work-open,.hang-open');
    if (!btn) return;
    var list = Array.prototype.slice.call(document.querySelectorAll('.plate,.work,.hang'));
    var fig = btn.closest('.plate,.work,.hang');
    open(list, list.indexOf(fig), btn);
  });
  lb.addEventListener('click', function (e) {
    var act = e.target.closest && e.target.closest('[data-act]');
    if (act){
      var a = act.getAttribute('data-act');
      if (a === 'close') close();
      else if (a === 'in') setScale(scale*1.5);
      else if (a === 'out') setScale(scale/1.5);
      else if (a === 'reset') setScale(1);
      else if (a === 'prev') show(index-1);
      else if (a === 'next') show(index+1);
      return;
    }
    if (e.target === stage) close();
  });
  document.addEventListener('keydown', function (e) {
    if (!lb.hasAttribute('open')) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowRight') show(index+1);
    else if (e.key === 'ArrowLeft') show(index-1);
    else if (e.key === '+' || e.key === '=') setScale(scale*1.5);
    else if (e.key === '-') setScale(scale/1.5);
    else if (e.key === '0') setScale(1);
  });
  stage.addEventListener('wheel', function (e) {
    if (!lb.hasAttribute('open')) return;
    e.preventDefault(); var p = stageXY(e);
    setScale(scale*(e.deltaY < 0 ? 1.16 : 1/1.16), p.x, p.y);
  }, {passive:false});
  stage.addEventListener('dblclick', function (e) { var p = stageXY(e); setScale(scale > 1.05 ? 1 : 2.5, p.x, p.y); });
  var pts = new Map(), dragging = false, lx = 0, ly = 0, pinch = null;
  stage.addEventListener('pointerdown', function (e) {
    if (e.target !== img) return;
    pts.set(e.pointerId, {x:e.clientX, y:e.clientY});
    if (pts.size === 1 && scale > MIN){ dragging = true; lx = e.clientX; ly = e.clientY; stage.classList.add('is-panning'); stage.setPointerCapture(e.pointerId); }
  });
  stage.addEventListener('pointermove', function (e) {
    if (!pts.has(e.pointerId)) return;
    pts.set(e.pointerId, {x:e.clientX, y:e.clientY});
    if (pts.size === 2){
      dragging = false;
      var a2 = Array.from(pts.values()), d = Math.hypot(a2[0].x-a2[1].x, a2[0].y-a2[1].y);
      if (!pinch) pinch = {d:d, s:scale}; else if (pinch.d > 0) setScale(pinch.s*(d/pinch.d));
    } else if (dragging){
      tx += e.clientX-lx; ty += e.clientY-ly; lx = e.clientX; ly = e.clientY; clampPan(); apply();
    }
  });
  function endPointer(e){
    pts.delete(e.pointerId);
    if (pts.size < 2) pinch = null;
    if (pts.size === 0){ dragging = false; stage.classList.remove('is-panning'); }
  }
  stage.addEventListener('pointerup', endPointer);
  stage.addEventListener('pointercancel', endPointer);
  window.addEventListener('resize', function () { if (lb.hasAttribute('open')){ measure(); clampPan(); apply(); } });
  labels();
})();

"""Build a self-contained page showing the motion ideas on the real assets.

Not part of the site and never published with it. It writes one HTML file with
the fonts, the seal and four pieces inlined, so it opens anywhere with nothing
alongside it - the point is to judge movement, which a description cannot carry.

Every picture is inlined exactly once, into a JS object, and the page assigns
them where they are needed. Inlining them at each use put several of them in
the file three times over and doubled its size.
"""
import base64
import os

OUT = ('/tmp/claude-0/-home-user-quotes/071e6230-7bb5-5595-b4c7-2f954253917a'
       '/scratchpad/motion.html')
PIECES = ['home_mark', 'lace_rosette', 'lace_sixpetal', 'cross_d']


def b64(path):
    return base64.b64encode(open(path, 'rb').read()).decode()


def data_uri(name):
    return 'data:image/webp;base64,' + b64(f'img/{name}.webp')


TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Motion ideas</title>
<style>
@font-face{font-family:'Fraunces';font-weight:600;font-display:swap;
  src:url(data:font/woff2;base64,__FONT_DISPLAY__) format('woff2');}
@font-face{font-family:'Manrope';font-weight:400;font-display:swap;
  src:url(data:font/woff2;base64,__FONT_BODY__) format('woff2');}
*,*::before,*::after{box-sizing:border-box;}
body{margin:0;background:#0f0d09;color:#fff;font:400 1rem/1.6 'Manrope',system-ui,sans-serif;
  -webkit-font-smoothing:antialiased;}
.wrap{max-width:58rem;margin:0 auto;padding:3rem 1.25rem 5rem;}
h1{font-family:'Fraunces',Georgia,serif;font-weight:600;
  font-size:clamp(1.8rem,5vw,2.6rem);margin:0 0 .4rem;}
.lede{color:rgba(255,255,255,.72);max-width:40rem;margin:0 0 1rem;}
section{border-top:1px solid rgba(255,255,255,.14);padding:2.4rem 0 0;margin-top:2.4rem;}
h2{font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:1.3rem;margin:0 0 .25rem;}
.why{color:rgba(255,255,255,.66);font-size:.92rem;margin:0 0 1.3rem;max-width:42rem;}
.stage{background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.1);
  border-radius:.4rem;padding:1.5rem;position:relative;overflow:hidden;}
button{font:inherit;font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;
  background:transparent;color:rgba(255,255,255,.8);border:1px solid rgba(255,255,255,.3);
  border-radius:999px;padding:.5rem .95rem;cursor:pointer;margin-top:1.1rem;}
button:hover{color:#fff;border-color:#fff;}
.tag{display:inline-block;font-size:.58rem;letter-spacing:.2em;text-transform:uppercase;
  color:#f0c9a4;border:1px solid rgba(240,201,164,.4);border-radius:999px;
  padding:.18rem .55rem;margin-left:.45rem;vertical-align:middle;}
.cost{font-size:.78rem;color:rgba(255,255,255,.5);margin-top:.9rem;}

/* 1 - the seal drawn like thread */
.seal-svg{width:11rem;height:11rem;color:rgba(255,255,255,.75);display:block;margin:0 auto;}
.drawing .seal-svg path,.drawing .seal-svg circle{
  stroke-dasharray:var(--len,600);stroke-dashoffset:var(--len,600);
  animation:draw 2.4s cubic-bezier(.33,.1,.25,1) forwards;
  animation-delay:calc(var(--i,0)*13ms);}
@keyframes draw{to{stroke-dashoffset:0;}}

/* 2 - crossing between pages */
.pages{position:relative;height:16rem;border-radius:.3rem;overflow:hidden;background:#17140e;}
.pg{position:absolute;inset:0;display:grid;place-items:center;text-align:center;
  background-size:cover;background-position:50% 50%;}
.pg::after{content:"";position:absolute;inset:0;background:rgba(10,9,6,.55);}
.pg h3{position:relative;z-index:1;font-family:'Fraunces',Georgia,serif;font-weight:600;
  font-size:1.7rem;margin:0;}
.pg.out{animation:pgout .62s cubic-bezier(.4,0,.2,1) forwards;}
.pg.in{animation:pgin .62s cubic-bezier(.4,0,.2,1) forwards;}
@keyframes pgout{to{opacity:0;transform:scale(1.015);}}
@keyframes pgin{from{opacity:0;transform:scale(.988);}to{opacity:1;transform:none;}}

/* 3 - the painting drifts slower than the words */
.par{height:18rem;overflow:auto;border-radius:.3rem;position:relative;background:#17140e;}
.par-bg{position:sticky;top:0;height:0;z-index:0;}
.par-bg i{display:block;height:18rem;background-size:cover;background-position:50% 40%;
  will-change:transform;opacity:.55;}
.par-body{position:relative;z-index:1;padding:4.5rem 1.4rem;}
.par-body p{background:rgba(10,9,6,.55);padding:.65rem .85rem;border-radius:.25rem;
  max-width:24rem;margin:0 0 .9rem;}

/* 4 - the cards arrive one after another */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(7.5rem,1fr));gap:.8rem;}
.card{background:rgba(233,225,207,.9);border-radius:.3rem;padding:.9rem;text-align:center;
  color:#1f1809;}
.card img{width:100%;height:4.6rem;object-fit:contain;display:block;}
.card b{display:block;font-family:'Fraunces',Georgia,serif;font-size:.85rem;margin-top:.45rem;}
.staggered .card{opacity:0;animation:rise .85s cubic-bezier(.19,1,.22,1) forwards;
  animation-delay:calc(var(--n)*110ms);}
@keyframes rise{from{opacity:0;transform:translateY(26px);}to{opacity:1;transform:none;}}

/* 5 - the piece grows out of where it sits */
.thumbs{display:flex;gap:1rem;flex-wrap:wrap;align-items:center;}
.thumbs img{width:6.2rem;cursor:zoom-in;transition:transform .4s;}
.thumbs img:hover{transform:translateY(-4px);}
.lb{position:fixed;inset:0;background:rgba(10,9,6,.92);display:none;place-items:center;
  z-index:40;cursor:zoom-out;}
.lb.on{display:grid;}
.lb img{max-width:76vw;max-height:76vh;}

.note{margin-top:2.6rem;border-top:1px solid rgba(255,255,255,.14);padding-top:1.4rem;
  color:rgba(255,255,255,.6);font-size:.88rem;}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important;}}
</style></head><body><div class="wrap">

<h1>Five motion ideas</h1>
<p class="lede">Each one running on the archive's own assets. Press the buttons to
replay. All of it is cheap, reversible, adds no file to download, and switches
off for anyone whose system asks for reduced motion &mdash; as the site's
existing movement already does.</p>

<section>
  <h2>1 &middot; The seal draws itself<span class="tag">my pick</span></h2>
  <p class="why">The mark in every footer is built from stroked paths, so it can be
  drawn rather than faded in: a line of thread laying itself down, which is how
  the work it stands for was made. It would happen once, when the foot of a page
  comes into view.</p>
  <div class="stage"><div id="sealbox">__SEAL__</div>
  <button onclick="drawSeal()">Draw again</button></div>
  <p class="cost">No new files. Fifteen lines of CSS, three of JavaScript.</p>
</section>

<section>
  <h2>2 &middot; Pages cross-fade instead of blinking</h2>
  <p class="why">Five pages share one painted ground, but moving between them is a
  hard reload: a white flash, then the page rebuilds. A cross-fade makes the
  archive feel like one place you move around in rather than five documents.</p>
  <div class="stage"><div class="pages" id="pages"></div>
  <button onclick="swapPage()">Go to the next page</button></div>
  <p class="cost">Browsers with view transitions get it; the rest keep today's
  behaviour, so no fallback is needed.</p>
</section>

<section>
  <h2>3 &middot; The painting drifts slower than the words</h2>
  <p class="why">The watercolour behind every page is fixed, so it sits dead still
  while you scroll. Letting it move at about a fifth of your speed gives the page
  depth without anyone working out why. Scroll inside the frame.</p>
  <div class="stage"><div class="par" id="par">
    <div class="par-bg"><i id="parbg"></i></div>
    <div class="par-body">
      <p>Scroll this panel.</p><p>The ground moves, but slowly.</p>
      <p>About a fifth of your speed.</p><p>Enough to feel, not to notice.</p>
      <p>One transform per frame.</p>
    </div>
  </div></div>
  <p class="cost">One scroll listener, one transform. Worth switching off on phones.</p>
</section>

<section>
  <h2>4 &middot; The collections arrive one after another</h2>
  <p class="why">The four cards currently fade in together. Bringing them in a tenth
  of a second apart reads as a hand laying them out, and draws the eye along the
  row instead of at the whole block at once.</p>
  <div class="stage"><div class="cards staggered" id="cards"></div>
  <button onclick="restagger()">Replay</button></div>
  <p class="cost">Four lines, using the reveal machinery already on the site.</p>
</section>

<section>
  <h2>5 &middot; A piece opens out of where it sits<span class="tag">my pick</span></h2>
  <p class="why">Opening a piece cuts straight to the viewer. Growing it out of the
  thumbnail keeps hold of which piece you clicked &mdash; which matters on a page of
  eleven near-identical doilies. Click one.</p>
  <div class="stage"><div class="thumbs" id="thumbs"></div></div>
  <p class="cost">About a dozen lines measuring the thumbnail and animating from it.
  Works with the zoom viewer already there.</p>
</section>

<p class="note">What I would not add: anything that moves while you are reading,
anything tied to the cursor, and text that animates in word by word. The pieces
should be the only things in the room that move.</p>
</div>

<div class="lb" id="lb" onclick="this.classList.remove('on')"><img id="lbimg" alt=""></div>

<script>
var IMG = __IMAGES__;
var PAGES = [['Four Collections','home_mark'],['Lace &amp; Doilies','lace_rosette'],
             ['Crosses','cross_d']];
var CARDS = [['Lace &amp; Doilies','lace_rosette'],['The Alphabet','home_mark'],
             ['Lace to Wear','lace_sixpetal'],['Crosses','cross_d']];
var pageAt = 0;

function drawSeal(){
  var box = document.getElementById('sealbox');
  box.classList.remove('drawing');
  var n = 0;
  box.querySelectorAll('path,circle').forEach(function(el){
    var len = 600;
    try { len = Math.ceil(el.getTotalLength()) || 600; } catch(e) {}
    el.style.setProperty('--len', len);
    el.style.setProperty('--i', n++);
  });
  void box.offsetWidth;
  box.classList.add('drawing');
}

function paintPage(i){
  var d = document.createElement('div');
  d.className = 'pg';
  d.style.backgroundImage = 'url(' + IMG[PAGES[i][1]] + ')';
  d.innerHTML = '<h3>' + PAGES[i][0] + '</h3>';
  return d;
}
function swapPage(){
  var host = document.getElementById('pages');
  var cur = host.querySelector('.pg');
  pageAt = (pageAt + 1) % PAGES.length;
  var next = paintPage(pageAt);
  next.classList.add('in');
  host.appendChild(next);
  if (cur) cur.classList.add('out');
  setTimeout(function(){ if (cur) cur.remove(); next.classList.remove('in'); }, 640);
}

function restagger(){
  var c = document.getElementById('cards');
  c.classList.remove('staggered'); void c.offsetWidth; c.classList.add('staggered');
}

function zoom(el){
  var lb = document.getElementById('lb'), big = document.getElementById('lbimg');
  big.src = el.src; lb.classList.add('on');
  var from = el.getBoundingClientRect();
  requestAnimationFrame(function(){
    var to = big.getBoundingClientRect();
    if (!to.width) return;
    var k = from.width / to.width;
    big.animate([
      {transform:'translate(' + (from.left + from.width/2 - (to.left + to.width/2)) + 'px,'
        + (from.top + from.height/2 - (to.top + to.height/2)) + 'px) scale(' + k + ')',
       opacity:.35},
      {transform:'none', opacity:1}
    ], {duration:460, easing:'cubic-bezier(.19,1,.22,1)'});
  });
}

// the ground drifts at a fifth of the scroll
var par = document.getElementById('par');
par.addEventListener('scroll', function(){
  document.getElementById('parbg').style.transform =
    'translateY(' + (par.scrollTop * 0.2).toFixed(1) + 'px)';
}, {passive:true});

// fill everything that needs a picture, from the one copy of each
document.getElementById('parbg').style.backgroundImage = 'url(' + IMG.lace_rosette + ')';
document.getElementById('pages').appendChild(paintPage(0));
document.getElementById('cards').innerHTML = CARDS.map(function(c, i){
  return '<div class="card" style="--n:' + i + '"><img src="' + IMG[c[1]] +
         '" alt=""><b>' + c[0] + '</b></div>';
}).join('');
document.getElementById('thumbs').innerHTML =
  ['lace_rosette','lace_sixpetal','cross_d'].map(function(k){
    return '<img src="' + IMG[k] + '" alt="" onclick="zoom(this)">';
  }).join('');
drawSeal();
</script></body></html>
'''


def main():
    images = ',\n  '.join(f'{n}: "{data_uri(n)}"' for n in PIECES)
    html = (TEMPLATE
            .replace('__FONT_DISPLAY__', b64('fonts/fraunces-600.woff2'))
            .replace('__FONT_BODY__', b64('fonts/manrope.woff2'))
            .replace('__SEAL__', open('seal.svg', encoding='utf-8')
                     .read().replace('<svg ', '<svg class="seal-svg" ', 1))
            .replace('__IMAGES__', '{\n  ' + images + '\n}'))
    open(OUT, 'w', encoding='utf-8').write(html)
    print(OUT, f'{os.path.getsize(OUT) / 1024:.0f} KB')


if __name__ == '__main__':
    main()

"""Pre-flight checks for dist/. Exits non-zero on anything that would ship broken.

Two halves. The static half reads the built files: links, ids, alt text,
headings, meta, orphaned assets. The live half drives Chromium over every page
in both languages at four window sizes, opens all twenty-seven pieces in the
zoom viewer, and watches for console errors, broken images, overflow and
unreachable controls.

Run it before every deploy:  python3 check_site.py
"""
import collections
import io
import json
import os
import re
import sys
import glob
import pathlib

OUT = '../dist'
VIEWPORTS = [(1440, 900, 'desktop'), (1024, 768, 'tablet'),
             (390, 844, 'phone'), (360, 640, 'small phone')]
CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'

fails, warns = [], []


def fail(page, msg):
    fails.append(f'{page}: {msg}')


def warn(page, msg):
    warns.append(f'{page}: {msg}')


# ---------------------------------------------------------------- static ----

def static_checks():
    pages = sorted(glob.glob(os.path.join(OUT, '*.html')))
    on_disk = {os.path.relpath(p, OUT).replace(os.sep, '/')
               for p in glob.glob(os.path.join(OUT, '**', '*'), recursive=True)
               if os.path.isfile(p)}
    referenced = set()

    for path in pages:
        name = os.path.basename(path)
        html = open(path, encoding='utf-8').read()

        # every local href/src/srcset points at a file that exists
        for attr in re.findall(
                r'(?:href|src|srcset|data-zoom|data-zoom-avif)="([^"]+)"', html):
            target = attr.split('#')[0].split('?')[0]
            if not target or target.startswith(('http', 'data:', 'mailto:', '#')):
                continue
            referenced.add(target)
            if target not in on_disk:
                fail(name, f'dead link or missing file: {target}')

        # the share card is named in a meta tag, not an href
        for og in re.findall(
                r'<meta[^>]+(?:property|name)="(?:og:image|twitter:image)"'
                r'[^>]+content="([^"]+)"', html):
            t = og.split('#')[0]
            if not t.startswith('http'):
                referenced.add(t)
                if t not in on_disk:
                    fail(name, f'share image is missing: {t}')

        # in-page anchors resolve
        for frag in re.findall(r'href="#([^"]+)"', html):
            if frag and f'id="{frag}"' not in html:
                fail(name, f'anchor #{frag} has no target')

        # ids are unique
        dupes = [i for i, n in collections.Counter(
            re.findall(r'\bid="([^"]+)"', html)).items() if n > 1]
        if dupes:
            fail(name, f'duplicate id: {dupes}')

        # every content image has alt text (decorative ones use alt="")
        for tag in re.findall(r'<img\b[^>]*>', html):
            if 'alt=' not in tag:
                fail(name, f'img with no alt attribute: {tag[:70]}')

        # exactly one h1, and no heading level skipped
        levels = [int(h) for h in re.findall(r'<h([1-6])\b', html)]
        h1s = levels.count(1)
        if h1s != 1:
            # both language copies of a heading are in the markup at once
            en = len(re.findall(r'<h1[^>]*\bi18n en\b', html))
            hy = len(re.findall(r'<h1[^>]*\bi18n hy\b', html))
            if not (en == hy == 1) and h1s != 1:
                fail(name, f'{h1s} h1 elements (expected one per language)')
        seen = set()
        for lv in levels:
            if lv > 1 and lv - 1 not in seen and lv not in seen:
                warn(name, f'heading level h{lv} appears before h{lv - 1}')
            seen.add(lv)

        # the things that make a link look right when it is shared
        for needle, what in [('<title', 'title'),
                             ('name="description"', 'meta description'),
                             ('property="og:image"', 'og:image'),
                             ('rel="icon"', 'favicon'),
                             ('lang=', 'html lang')]:
            if needle not in html:
                fail(name, f'missing {what}')

        # a <picture> must keep a plain <img> inside it as the fallback. The
        # zoom viewer's picture is a template - the JS fills both the source
        # and the img when a piece is opened - so it has no urls to check here.
        for pic in re.findall(r'<picture>.*?</picture>', html, re.S):
            if 'lb-img' in pic:
                continue
            if '<img' not in pic:
                fail(name, 'picture element with no img fallback')
            if 'type="image/avif"' in pic and '.webp' not in pic:
                fail(name, 'picture offers avif with no webp fallback')

        # only pages with a gallery have anything worth deferring
        if html.count('<img') > 2 and 'loading="lazy"' not in html:
            warn(name, 'no lazily loaded images')

    # assets nobody asks for
    css = ''.join(open(p, encoding='utf-8').read()
                  for p in glob.glob(os.path.join(OUT, 'assets', '*.css')))
    # optimize_images.py and build_static.py both keep files on purpose that
    # the current pages do not name: the last few hashed stylesheets, so a
    # page still in someone's cache can find the CSS it was built against,
    # and the manifest that records their order.
    keep = set(json.load(open(os.path.join(OUT, 'assets', 'manifest.json'))))
    keep.add('manifest.json')
    for f in sorted(on_disk):
        if f.endswith(('.html', '.txt', '.xml', '_headers')) or '/' not in f:
            continue
        if f.startswith('assets/') and f.rsplit('/', 1)[-1] in keep:
            continue
        base = f.rsplit('/', 1)[-1]
        if f not in referenced and base not in css and f.rsplit('.', 1)[0] not in css:
            # an avif is reached through <source srcset>, which is covered above
            warn('dist', f'file nothing references: {f}')

    print(f'  read {len(pages)} pages, {len(on_disk)} files')



def _lum(c):
    def f(v):
        v /= 255
        return v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4
    r, g, b = [f(x) for x in c]
    return .2126 * r + .7152 * g + .0722 * b


def contrast(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + .05) / (lo + .05)


def check_contrast(pg, where):
    """Text over a painted backdrop, measured on the pixels the browser drew.

    Every page lays cream type over a photograph, so legibility depends on the
    particular painting behind it. Computing it from the stylesheet would miss
    that entirely - this samples the screenshot.
    """
    from PIL import Image
    boxes = pg.evaluate("""() => [...document.querySelectorAll(
        '.hang-title,.num,.prologue,.card-desc,.years p,.meta,.sign,figcaption p')]
      .filter(e => e.offsetParent && e.innerText.trim())
      .map(e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
        return {cls: e.className.split(' ')[0], t: e.innerText.trim().slice(0, 20),
                x: r.x, y: r.y, w: r.width, h: r.height,
                col: s.color, fs: parseFloat(s.fontSize),
                bold: parseInt(s.fontWeight) >= 700}; })
      .filter(b => b.y > 0 && b.y < window.innerHeight - 40 && b.w > 10)""")
    if not boxes:
        return
    shot = Image.open(io.BytesIO(pg.screenshot())).convert('RGB')
    for b in boxes:
        x, y, w, h = (int(b[k]) for k in 'xywh')
        crop = shot.crop((max(0, x), max(0, y),
                          min(shot.width, x + w), min(shot.height, y + h)))
        px = sorted(crop.getdata(), key=sum)
        if not px:
            continue
        bg = px[len(px) // 4]          # the glyphs are the light minority
        m = b['col'].replace('rgba(', '').replace('rgb(', '').replace(')', '').split(',')
        a = float(m[3]) if len(m) > 3 else 1.0
        fg = tuple(round(a * float(m[i]) + (1 - a) * bg[i]) for i in range(3))
        large = b['fs'] >= 24 or (b['fs'] >= 18.66 and b['bold'])
        need = 3.0 if large else 4.5
        got = contrast(fg, bg)
        if got < need:
            fail(where, f'contrast {got:.1f}:1 needs {need} - '
                        f'{b["cls"]} {b["fs"]:.0f}px "{b["t"]}"')
        elif got < need + 0.4:
            warn(where, f'contrast {got:.1f}:1 only just clears {need} - '
                        f'{b["cls"]} "{b["t"]}"')


# ------------------------------------------------------------------ live ----

PROBE = r"""() => {
  const vis = el => { const s = getComputedStyle(el);
    return s.display !== 'none' && s.visibility !== 'hidden'; };
  const out = {};
  out.brokenImg = [...document.images]
    .filter(i => i.currentSrc && i.complete && i.naturalWidth === 0)
    .map(i => i.currentSrc.split('/').pop());
  out.overflow = document.documentElement.scrollWidth > window.innerWidth + 1;
  out.wideEls = [...document.querySelectorAll('body *')]
    .filter(e => e.getBoundingClientRect().right > window.innerWidth + 2)
    .slice(0, 3).map(e => e.tagName + '.' + String(e.className).slice(0, 30));
  out.h1 = [...document.querySelectorAll('h1')].filter(vis).map(e => e.innerText.trim());
  // both language copies must never be on screen together
  out.bothLangs = [...document.querySelectorAll('.i18n.en')]
    .filter(e => vis(e) && document.documentElement.dataset.lang === 'hy').length
    + [...document.querySelectorAll('.i18n.hy')]
    .filter(e => vis(e) && document.documentElement.dataset.lang === 'en').length;
  // anything interactive must be big enough to hit with a thumb
  out.small = [...document.querySelectorAll('a,button')].filter(el => {
    if (!vis(el)) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && (r.width < 24 || r.height < 24);
  }).map(el => el.tagName + '.' + String(el.className).slice(0, 24)).slice(0, 5);
  return out;
}"""


def live_checks():
    from playwright.sync_api import sync_playwright
    root = pathlib.Path(OUT).resolve()
    pages = sorted(p.name for p in root.glob('*.html'))
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        for name in pages:
            for w, h, label in VIEWPORTS:
                for lang in ('en', 'hy'):
                    pg = br.new_page(viewport={'width': w, 'height': h})
                    errs, bad = [], []
                    pg.on('pageerror', lambda e: errs.append(str(e)))
                    pg.on('console', lambda m: errs.append(m.text)
                          if m.type == 'error' else None)
                    pg.on('response', lambda r: bad.append(f'{r.status} {r.url.split("/")[-1]}')
                          if r.status >= 400 else None)
                    pg.goto((root / name).as_uri())
                    pg.wait_for_timeout(350)
                    if lang == 'hy':
                        btn = pg.query_selector('.lang-btn[data-set="hy"]')
                        if not btn:
                            fail(name, 'no language switch')
                            pg.close()
                            continue
                        btn.click()
                        pg.wait_for_timeout(250)
                    for _ in range(24):
                        pg.mouse.wheel(0, 1100)
                        pg.wait_for_timeout(60)
                    pg.wait_for_timeout(500)

                    r = pg.evaluate(PROBE)
                    where = f'{name} [{label} {lang}]'
                    if errs:
                        fail(where, f'console: {errs[:2]}')
                    if bad:
                        fail(where, f'failed requests: {sorted(set(bad))[:3]}')
                    if r['brokenImg']:
                        fail(where, f'images that did not decode: {r["brokenImg"][:3]}')
                    if r['overflow']:
                        fail(where, f'page scrolls sideways; widest: {r["wideEls"]}')
                    if len(r['h1']) != 1:
                        fail(where, f'{len(r["h1"])} visible h1: {r["h1"]}')
                    if r['bothLangs']:
                        fail(where, f'{r["bothLangs"]} elements showing the wrong language')
                    if label == 'desktop' and lang == 'en':
                        check_contrast(pg, where)
                    if r['small'] and label.endswith('phone'):
                        warn(where, f'tap targets under 24px: {r["small"]}')
                    pg.close()

        # the zoom viewer, on every piece, at the two extremes
        for name in pages:
            for w, h, label in [(1440, 900, 'desktop'), (390, 844, 'phone')]:
                pg = br.new_page(viewport={'width': w, 'height': h})
                errs = []
                pg.on('pageerror', lambda e: errs.append(str(e)))
                pg.goto((root / name).as_uri())
                pg.wait_for_timeout(300)
                n = pg.evaluate("document.querySelectorAll('[data-zoom]').length")
                for i in range(n):
                    pg.evaluate(f"document.querySelectorAll('[data-zoom]')[{i}].click()")
                    pg.wait_for_timeout(420)
                    st = pg.evaluate("""() => {
                      const im = document.querySelector('.lb-img');
                      const stg = document.querySelector('.lb-stage');
                      if (!im || !stg) return {err: 'no viewer'};
                      const a = im.getBoundingClientRect(), s = stg.getBoundingClientRect();
                      return {open: document.querySelector('.lb').getAttribute('aria-hidden') === 'false',
                              loaded: im.naturalWidth > 0,
                              cropped: a.height > s.height + 1 || a.width > s.width + 1,
                              src: (im.currentSrc || '').split('/').pop()};
                    }""")
                    tag = f'{name} [{label}] piece {i + 1}'
                    if st.get('err'):
                        fail(tag, st['err'])
                    else:
                        if not st['open']:
                            fail(tag, 'zoom viewer did not open')
                        if not st['loaded']:
                            fail(tag, f'zoom image did not load ({st["src"]})')
                        if st['cropped']:
                            fail(tag, 'zoom image is cropped by the stage')
                    pg.keyboard.press('Escape')
                    pg.wait_for_timeout(180)
                if errs:
                    fail(f'{name} [{label}] zoom', f'console: {errs[:2]}')
                if n:
                    print(f'  {name:14} {label:8} opened {n} pieces')
                pg.close()

        # keyboard: you must be able to reach and use the page without a mouse
        pg = br.new_page(viewport={'width': 1440, 'height': 900})
        pg.goto((root / 'doilies.html').as_uri())
        pg.wait_for_timeout(300)
        reached = []
        for _ in range(12):
            pg.keyboard.press('Tab')
            reached.append(pg.evaluate(
                "()=>{const a=document.activeElement;"
                "return a.tagName+'.'+String(a.className).slice(0,20);}"))
        if not any('lang-btn' in r or 'home-link' in r for r in reached):
            fail('doilies.html', 'language switch and nav are not reachable by keyboard')
        pg.keyboard.press('Enter')
        pg.wait_for_timeout(400)
        pg.close()
        br.close()


if __name__ == '__main__':
    print('static checks')
    static_checks()
    print('live checks')
    live_checks()
    print()
    for w in warns:
        print('  warn  ', w)
    for f in fails:
        print('  FAIL  ', f)
    print(f'\n{len(fails)} failures, {len(warns)} warnings')
    sys.exit(1 if fails else 0)

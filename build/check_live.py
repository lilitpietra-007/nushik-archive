"""Check the published site over HTTPS, the way a visitor reaches it.

check_site.py reads dist/ on disk and drives Chromium over local files. That
catches everything about the pages themselves, but it cannot see anything the
host does: the certificate, the redirects, the caching headers, whether the
share card is actually reachable at the absolute URL the pages advertise. This
checks that half.

    python3 check_live.py https://nushikmalkhasyan.com

It is read-only: it fetches pages and looks at them. Nothing is published,
changed or deleted.
"""
import glob
import re
import ssl
import sys
import urllib.error
import urllib.request

PAGES = ['', 'doilies.html', 'alphabet.html', 'wear.html', 'small.html',
         'life.html']
VIEWPORTS = [(1440, 900, 'desktop'), (390, 844, 'phone')]
UA = 'nushik-archive-checker'      # no personal detail: this goes to a server

problems = []
notes = []


def fail(msg):
    problems.append(msg)
    print(f'  FAIL  {msg}')


def note(msg):
    notes.append(msg)
    print(f'  note  {msg}')


def _chrome():
    """The bundled Chromium, found rather than hard-coded - see check_site.py."""
    for pat in ('/opt/pw-browsers/chromium-*/chrome-linux*/chrome',
                '/opt/pw-browsers/chromium/chrome-linux*/chrome',
                '/opt/pw-browsers/chromium_headless_shell-*/'
                'chrome-headless-shell-linux*/chrome-headless-shell'):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    return None


def get(url, method='GET'):
    """Fetch a URL, following redirects. Returns (status, headers, body, final)."""
    req = urllib.request.Request(url, method=method,
                                 headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read() if method == 'GET' else b''
            return r.status, dict(r.headers), body, r.url
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read(), url
    except (urllib.error.URLError, ssl.SSLError, TimeoutError) as e:
        return None, {}, str(e).encode(), url


def check_reachable(base):
    """The certificate, and that the site answers at all."""
    print('reachable')
    status, hdrs, body, final = get(base + '/')
    if status is None:
        fail(f'{base} did not answer: {body.decode(errors="replace")[:200]}')
        return False
    if status != 200:
        fail(f'{base}/ returned {status}')
        return False
    print(f'  served over {final.split(":")[0]}, {len(body) / 1024:.0f} KB of HTML')
    if not final.startswith('https://'):
        fail(f'{base}/ did not end up on https (landed on {final})')
    return True


def check_http_redirect(host):
    """Plain http should end up on https, not serve the site unencrypted."""
    print('http -> https')
    status, hdrs, body, final = get(f'http://{host}/')
    if status is None:
        note(f'http://{host}/ did not answer at all '
             f'({body.decode(errors="replace")[:120]})')
        return
    if final.startswith('https://'):
        print(f'  http redirects to {final}')
    else:
        fail(f'http://{host}/ stayed on http (landed on {final}) - the site is '
             f'reachable unencrypted')


def check_pages(base):
    """Every page answers 200, and says it is the page it should be."""
    print('pages')
    for p in PAGES:
        url = f'{base}/{p}'
        status, hdrs, body, final = get(url)
        name = p or 'index.html'
        if status != 200:
            fail(f'{name} returned {status}')
            continue
        html = body.decode('utf-8', errors='replace')

        ok = True
        canon = re.search(r'<link rel="canonical" href="([^"]+)"', html)
        if not canon:
            fail(f'{name} has no canonical link')
            ok = False
        elif not canon.group(1).startswith(base):
            fail(f'{name} canonical points elsewhere: {canon.group(1)} '
                 f'- SITE_URL in build_static.py is out of date')
            ok = False

        if 'noindex' in html:
            fail(f'{name} still carries noindex')
            ok = False
        if ok:
            print(f'  {name:14} 200, canonical ok')


def check_headers(base):
    """The caching rules in dist/_headers - the reason for leaving GitHub Pages.

    A hashed asset must be immutable for a year, a page must not be cached at
    all. If these are missing the site still works, but every visit re-fetches
    the fonts and the stylesheet.
    """
    print('caching headers')
    status, hdrs, body, final = get(base + '/')
    html = body.decode('utf-8', errors='replace')

    css = re.search(r'href="(assets/site\.[a-f0-9]+\.css)"', html)
    img = re.search(r'src="(img/[A-Za-z0-9_.-]+\.(?:webp|avif))"', html)

    page_cc = hdrs.get('Cache-Control', '')
    if 'max-age=0' in page_cc or 'no-cache' in page_cc or 'must-revalidate' in page_cc:
        print(f'  page      {page_cc}')
    else:
        fail(f'the page is cached as "{page_cc or "(nothing)"}" - a visitor can '
             f'be served a stale page with no way to purge it')

    if css:
        s, h, _, _ = get(f'{base}/{css.group(1)}', method='HEAD')
        cc = h.get('Cache-Control', '')
        if 'immutable' in cc and 'max-age=31536000' in cc:
            print(f'  stylesheet {cc}')
        else:
            fail(f'the stylesheet is cached as "{cc or "(nothing)"}" - _headers '
                 f'is not being applied')
    else:
        note('no hashed stylesheet found on the home page to check')

    if img:
        s, h, _, _ = get(f'{base}/{img.group(1)}', method='HEAD')
        cc = h.get('Cache-Control', '')
        print(f'  image      {cc or "(nothing)"}')
        if 'max-age' not in cc:
            note('images carry no max-age; they will be re-fetched more than needed')


def check_extras(base):
    """robots.txt, sitemap.xml, the share card, and the 404 page."""
    print('the rest')
    for path, want in (('robots.txt', 'text'), ('sitemap.xml', 'xml')):
        status, hdrs, body, final = get(f'{base}/{path}')
        if status != 200:
            fail(f'{path} returned {status}')
            continue
        text = body.decode('utf-8', errors='replace')
        if base not in text:
            fail(f'{path} does not mention {base} - it was built for another '
                 f'address')
        else:
            print(f'  {path:12} 200, points at this domain')

    # the share card, at the absolute URL the pages advertise to Facebook etc.
    status, hdrs, body, final = get(f'{base}/')
    html = body.decode('utf-8', errors='replace')
    og = re.search(r'<meta property="og:image" content="([^"]+)"', html)
    if not og:
        fail('the home page has no og:image')
    else:
        s, h, b, _ = get(og.group(1), method='HEAD')
        if s != 200:
            fail(f'the share card at {og.group(1)} returned {s} - link previews '
                 f'will be blank')
        else:
            print(f'  share card   200, {h.get("Content-Type", "?")}')

    status, hdrs, body, final = get(f'{base}/no-such-page-here')
    if status != 404:
        fail(f'a missing address returned {status}, not 404')
    elif b'Nushik' not in body and 'Նուշիկ'.encode() not in body:
        note(f'the 404 page answered {status} but does not look like the '
             f'site\'s own 404 page')
    else:
        print('  404 page     404, the site\'s own')


def check_rendered(base):
    """Open the real pages in a browser: images, console errors, the viewer."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        note('playwright is not installed here, so the rendering checks were '
             'skipped; the fetch checks above still ran')
        return
    print('rendered')
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=_chrome())
        for w, h, label in VIEWPORTS:
            for page in PAGES:
                ctx = b.new_context(viewport={'width': w, 'height': h})
                pg = ctx.new_page()
                errs, bad = [], []
                pg.on('pageerror', lambda e: errs.append(str(e)))
                pg.on('response',
                      lambda r: bad.append(f'{r.status} {r.url}')
                      if r.status >= 400 else None)
                try:
                    pg.goto(f'{base}/{page}', wait_until='load', timeout=45000)
                except Exception as e:
                    fail(f'{page or "index.html"} ({label}) would not load: {e}')
                    ctx.close()
                    continue
                pg.wait_for_timeout(900)
                for _ in range(22):
                    pg.mouse.wheel(0, 1300)
                    pg.wait_for_timeout(60)
                pg.wait_for_timeout(1200)
                broken = pg.evaluate(
                    "()=>[...document.images].filter("
                    "i=>i.currentSrc&&i.complete&&!i.naturalWidth).length")
                over = pg.evaluate(
                    "()=>document.documentElement.scrollWidth>"
                    "document.documentElement.clientWidth+2")
                name = page or 'index.html'
                if errs:
                    fail(f'{name} ({label}) console error: {errs[0][:160]}')
                if bad:
                    fail(f'{name} ({label}) fetch failed: {bad[0]}')
                if broken:
                    fail(f'{name} ({label}) has {broken} image(s) that did not decode')
                if over:
                    fail(f'{name} ({label}) scrolls sideways')
                if not (errs or bad or broken or over):
                    print(f'  {name:14} {label:8} clean')
                ctx.close()

        # the zoom viewer, on the page with the most pieces
        ctx = b.new_context(viewport={'width': 1440, 'height': 900})
        pg = ctx.new_page()
        pg.goto(f'{base}/doilies.html', wait_until='load', timeout=45000)
        pg.wait_for_timeout(900)
        pg.evaluate("document.querySelector('[data-zoom]').click()")
        pg.wait_for_timeout(1800)
        shown = pg.evaluate(
            "()=>{const i=document.querySelector('.lb-img');"
            "return i?{loaded:i.naturalWidth>0,"
            "src:(i.currentSrc||'').split('/').pop()}:null;}")
        if not shown or not shown['loaded']:
            fail('the zoom viewer did not load its image')
        else:
            print(f'  zoom viewer    opened {shown["src"]}')
        ctx.close()
        b.close()


def main():
    if len(sys.argv) < 2:
        sys.exit('usage: python3 check_live.py https://your-domain')
    base = sys.argv[1].rstrip('/')
    host = re.sub(r'^https?://', '', base)
    print(f'checking {base}\n')

    if not check_reachable(base):
        sys.exit('\nthe site did not answer, so nothing else was checked')
    check_http_redirect(host)
    check_pages(base)
    check_headers(base)
    check_extras(base)
    check_rendered(base)

    print()
    if problems:
        print(f'{len(problems)} problem(s), {len(notes)} note(s)')
        for m in problems:
            print(f'  - {m}')
        sys.exit(1)
    print(f'all clear, {len(notes)} note(s)')


if __name__ == '__main__':
    main()

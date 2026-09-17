"""Build the public website into dist/.

The Artifact build packs everything into one 14 MB file, which is right for a
single shareable link and wrong for a website: a visitor downloads all four
collections' photographs before the first word appears. Here each collection is
a real page at its own URL, images are files the browser caches and lazy-loads,
and the text is real UTF-8 Armenian rather than numeric entities - so it can be
selected, searched, and indexed.
"""
import base64, hashlib, json, os, re, shutil, sys
from PIL import Image

# The domain you launch on, once you have one - e.g. 'https://nushikmalkhasyan.com'.
# Leave it empty and the site still works everywhere; it just ships without the
# canonical link and the sitemap, both of which have to name a real domain to
# mean anything. Never point them at a domain you do not own.
SITE_URL = ''

# The Armenian on the site is still an unreviewed first draft and twenty-one
# strings carry visible [square-bracket] placeholders. Until that is fixed the
# pages ask search engines to stay away, so a live preview cannot be indexed
# under her name. Flip to True once the text is final and rebuild.
INDEXABLE = False

# build/ and dist/ are siblings, so the output goes up one level
IMG, OUT = 'img', '../dist'

PAGES = [
    # file            body source            backdrop   title EN / HY, description
    ('index.html',    '_home_body.html',     'cottage',
     'Nushik Malkhasyan — Needlework from Dilijan', 'Նուշիկ Մալխասյան',
     'A bilingual archive of twenty-seven pieces of hand needlework by Nushik '
     'Malkhasyan of Dilijan, Armenia — lace, doilies, the Armenian alphabet, '
     'collars, gloves and crosses.'),
    ('doilies.html',  'body2.html',          'cottage',
     'Lace & Doilies — Nushik Malkhasyan', 'Ժանյակ և անձեռոցիկ',
     'Eleven table pieces in hand-worked lace: rosettes, medallion wheels, and '
     'the lettered oval Nushik Malkhasyan dated 2005.'),
    ('alphabet.html', 'template_alpha.html', 'meadow',
     'The Armenian Alphabet — Nushik Malkhasyan', 'Հայոց այբուբենը',
     'All thirty-eight letters of the Armenian alphabet, once in filet lace and '
     'once embroidered, marking the 1600 years from 405 to 2005.'),
    ('wear.html',     'template_wear.html',  'portrait',
     'Lace to Wear — Nushik Malkhasyan', 'Ժանյակ՝ կրելու համար',
     'Collars and gloves in hand-worked lace — the pieces that had to fit a '
     'person rather than a table.'),
    ('small.html',    '_small_body.html',    'cottage',
     'Crosses & Small Pieces — Nushik Malkhasyan', 'Խաչեր և փոքր գործեր',
     'Four lace crosses, three of them edged in gold thread, and five small '
     'rounds — shown hanging on threads, the way lace is worked.'),
]

BACKDROP = {'cottage': 'cottage.webp', 'meadow': 'meadow.webp', 'portrait': 'portrait.webp'}

TOK = {
 '__LACE_ROSETTE__':'lace_rosette','__LACE_ROSETTE2__':'lace_rosette2','__LACE_MEDALLION__':'lace_medallion',
 '__LACE_STAR__':'lace_star','__LACE_OVAL__':'lace_oval','__LACE_CONCENTRIC__':'lace_concentric',
 '__LACE_SPIRAL_ROUND__':'lace_spiral_round','__LACE_SPIRAL_OVAL__':'lace_spiral_oval',
 '__LACE_SCALLOP__':'lace_scallop','__LACE_SIXMEDALLION__':'lace_sixmedallion','__LACE_SIXPETAL__':'lace_sixpetal',
 '__ZOOM_ROSETTE__':'lace_rosette_zoom','__ZOOM_ROSETTE2__':'lace_rosette2_zoom','__ZOOM_MEDALLION__':'lace_medallion_zoom',
 '__ZOOM_STAR__':'lace_star_zoom','__ZOOM_OVAL__':'lace_oval_zoom','__ZOOM_CONCENTRIC__':'lace_concentric_zoom',
 '__ZOOM_SPIRAL_ROUND__':'lace_spiral_round_zoom','__ZOOM_SPIRAL_OVAL__':'lace_spiral_oval_zoom',
 '__ZOOM_SCALLOP__':'lace_scallop_zoom','__ZOOM_SIXMEDALLION__':'lace_sixmedallion_zoom','__ZOOM_SIXPETAL__':'lace_sixpetal_zoom',
 '__ALPHA_LACE__':'alpha_lace_cut','__ALPHA_EMB__':'alpha_embroidery_cut',
 '__ZOOM_LACE__':'alpha_lace_zoom','__ZOOM_EMB__':'alpha_embroidery_zoom',
 '__WEAR_COLLAR_MESH__':'wear_collar_mesh','__WEAR_COLLAR_CROWN__':'wear_collar_crown',
 '__WEAR_COLLAR_NET__':'wear_collar_net','__WEAR_GLOVE_CREAM__':'wear_glove_cream','__WEAR_GLOVE_BLACK__':'wear_glove_black',
 '__ZOOM_COLLAR_MESH__':'wear_collar_mesh_zoom','__ZOOM_COLLAR_CROWN__':'wear_collar_crown_zoom',
 '__ZOOM_COLLAR_NET__':'wear_collar_net_zoom','__ZOOM_GLOVE_CREAM__':'wear_glove_cream_zoom',
 '__ZOOM_GLOVE_BLACK__':'wear_glove_black_zoom',
 '__HOME_MARK__':'home_mark','__CARD_DOILIES__':'lace_rosette',
 '__CARD_ALPHABET__':'alpha_lace_cut','__CARD_WEAR__':'wear_collar_crown','__CARD_SMALL__':'cross_d',
}
URLS = {'__URL_DOILIES__':'doilies.html', '__URL_ALPHABET__':'alphabet.html',
        '__URL_WEAR__':'wear.html', '__URL_SMALL__':'small.html', '__URL_HOME__':'index.html'}
OLD_ARTIFACTS = {'199465ee-19c1-4262-b5b8-03e0cf23ef81':'index.html',
                 '287dbf6f-3eec-4f5c-89d6-60f93c21d2bb':'doilies.html',
                 '475d63c2-c019-4632-b99b-6d9d717d22d6':'alphabet.html',
                 '7b0a5f55-556a-4595-a6e4-e0336d9eb207':'wear.html'}

used = set()
_dims = {}
_first = [True]


def dims(key):
    """Real pixel size, so the page reserves the space before the image lands."""
    if key not in _dims:
        with Image.open(os.path.join(IMG, key + '.webp')) as im:
            _dims[key] = im.size
    return _dims[key]


def deref(html, first_img=None):
    first_img = first_img if first_img is not None else _first
    html = re.sub(r'\s*<a class="home-link".*?</a>\n?', '', html, flags=re.S)
    html = html.replace(' loading="lazy"', '')

    def as_img(m):
        key = TOK[m.group(1)]
        used.add(key)
        w, h = dims(key)
        # the first image on a page is what the visitor is waiting for; the rest
        # can wait until they scroll
        lazy = '' if first_img[0] else ' loading="lazy" decoding="async"'
        first_img[0] = False
        return f'src="img/{key}.webp" width="{w}" height="{h}"{lazy}'

    html = re.sub(r'src="data:image/[a-z]+;base64,(__[A-Z0-9_]+__)"', as_img, html)

    def as_zoom(m):
        key = TOK[m.group(1)]
        used.add(key)
        return f'data-zoom="img/{key}.webp"'

    html = re.sub(r'data-zoom="data:image/[a-z]+;base64,(__[A-Z0-9_]+__)"', as_zoom, html)

    # the hanging page names its assets directly instead of through a token
    def as_named(m):
        key = m.group(1)
        used.add(key)
        w, h = dims(key)
        lazy = '' if first_img[0] else ' loading="lazy" decoding="async"'
        first_img[0] = False
        return f'src="img/{key}.webp" width="{w}" height="{h}"{lazy}'

    html = re.sub(r'data-img="([a-z0-9_]+)"', as_named, html)
    html = re.sub(r'data-zoom-img="([a-z0-9_]+)"',
                  lambda m: (used.add(m.group(1)) or f'data-zoom="img/{m.group(1)}.webp"'), html)
    for tok, href in URLS.items():
        html = html.replace(tok, href)
    for aid, href in OLD_ARTIFACTS.items():
        html = html.replace('https://claude.ai/code/artifact/' + aid, href)
    left = re.findall(r'__[A-Z0-9_]+__', html)
    if left:
        sys.exit('unmapped tokens: ' + str(sorted(set(left))))
    return html


def body_of(path):
    _first[0] = True
    s = open(path, encoding='utf-8').read()
    m = re.search(r'<div class="page">.*?\n</div>', s, re.S)
    if not m:
        sys.exit('no .page block in ' + path)
    return deref(m.group(0))


def build_css():
    css = open('template3.html', encoding='utf-8').read().partition('</style>')[0].split('<style>', 1)[1]
    for extra in ['i18n.css', 'lightbox.css', 'nav.css', 'spa_extra.css',
                  'spa_home.css', 'spa_hang.css', 'spa_dark.css',
                  'spa_rhythm.css', 'seal.css']:
        css += open(extra, encoding='utf-8').read()
    css = css.replace('    background-image:url("data:image/jpeg;base64,__COTTAGE__");\n', '')
    # fonts become cacheable files instead of a megabyte of base64 per page
    for tok, fn in [('__FONT_FRAUNCES__','fraunces-600'), ('__FONT_FRAUNCES_ITALIC__','fraunces-500i'),
                    ('__FONT_EBGARAMOND__','ebgaramond-400'), ('__FONT_BEAURIVAGE__','beaurivage'),
                    ('__FONT_NOTOARM__','noto-arm-400'), ('__FONT_MANROPE__','manrope'),
                    ('__FONT_NOTOSANSARM__','noto-sans-arm')]:
        css = css.replace('url(data:font/woff2;base64,%s)' % tok, "url('../fonts/%s.woff2')" % fn)
    if '__FONT' in css:
        sys.exit('a font token was not rewritten')
    css += '\n  /* page grounds */\n'
    for name, fn in BACKDROP.items():
        ids = ','.join('#view-%s > .backdrop' % os.path.splitext(p[0])[0].replace('index', 'home')
                       for p in PAGES if p[2] == name)
        css += '  %s{background-image:url("../img/%s");}\n' % (ids, fn)
    # every page carries exactly one view, always shown
    css += '  .view{display:block;}\n'
    bal = css.count('{') - css.count('}')
    if bal:
        sys.exit(f'unbalanced CSS: {bal:+d}')
    # a stray */ leaves garbage the parser silently swallows along with the
    # rules that follow it, and the brace count stays balanced through it
    if css.count('/*') != css.count('*/'):
        sys.exit(f"unbalanced CSS comments: {css.count('/*')} open, {css.count('*/')} close")
    return css


def head(fname, title_en, title_hy, desc, canonical, css_name, js_name):
    site = (f'<link rel="canonical" href="{canonical}">\n'
            f'<meta property="og:url" content="{canonical}">\n') if SITE_URL else ''
    if not INDEXABLE:
        site += '<meta name="robots" content="noindex, nofollow">\n'
    share = (SITE_URL + '/img/share.jpg') if SITE_URL else 'img/share.jpg'
    return f'''<!doctype html>
<html lang="en" data-lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title data-en="{title_en}" data-hy="{title_hy}">{title_en}</title>
<meta name="description" content="{desc}">
{site}<meta property="og:type" content="website">
<meta property="og:site_name" content="Nushik Malkhasyan">
<meta property="og:title" content="{title_en}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{share}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="stylesheet" href="assets/{css_name}">
</head>
<body>
'''


# How many earlier stylesheets and scripts to keep beside the current pair.
# The names carry a content hash, so a new build always writes a new name and
# used to delete the old one - which broke the site for anyone holding a
# cached page: GitHub Pages serves HTML with max-age=600, so for ten minutes
# after a deploy a returning visitor asked for a stylesheet that had just been
# removed, got a 404, and saw the page with no styling at all. Keeping the
# last few means stale HTML still finds the CSS it was built against. They are
# about 50 KB a pair.
KEEP_ASSETS = 5


def previous_assets():
    """The asset files from the last build, as {name: text}, newest first.

    The order is remembered in a manifest rather than read off the
    filesystem, because a fresh clone gives every file the same mtime.
    """
    adir = os.path.join(OUT, 'assets')
    if not os.path.isdir(adir):
        return {}
    try:
        order = json.load(open(os.path.join(adir, 'manifest.json')))
    except (OSError, ValueError):
        order = sorted(os.listdir(adir))
    keep = {}
    for name in order:
        path = os.path.join(adir, name)
        if name != 'manifest.json' and os.path.isfile(path):
            keep[name] = open(path, encoding='utf-8').read()
    return keep


def main():
    old_assets = previous_assets()
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, 'assets'))
    os.makedirs(os.path.join(OUT, 'img'))
    os.makedirs(os.path.join(OUT, 'fonts'))

    nav_lang = ('<div class="lang" role="group" aria-label="Language / Լեզու">\n'
                '  <button type="button" class="lang-btn" data-set="hy" lang="hy" aria-pressed="false">ՀԱՅ</button>\n'
                '  <button type="button" class="lang-btn" data-set="en" aria-pressed="true">ENG</button>\n'
                '</div>\n')
    home_link = ('<a class="home-link" href="index.html">\n'
                 '  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" '
                 'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
                 '<path d="M15 5l-7 7 7 7"/></svg>\n'
                 '  <span class="i18n en">Archive</span>'
                 '<span class="i18n hy" lang="hy">Արխիվ</span>\n</a>\n')
    lightbox = open('spa_lightbox.html', encoding='utf-8').read()
    seal = open('seal.html', encoding='utf-8').read()

    css, js = build_css(), open('site.js', encoding='utf-8').read()
    def stamped(name, text):
        h = hashlib.sha256(text.encode()).hexdigest()[:8]
        base, ext = name.rsplit('.', 1)
        fn = f'{base}.{h}.{ext}'
        open(os.path.join(OUT, 'assets', fn), 'w', encoding='utf-8').write(text)
        return fn
    css_name, js_name = stamped('site.css', css), stamped('site.js', js)

    # put the previous builds' assets back beside the new pair, newest first,
    # so pages still in someone's cache keep working
    order = [css_name, js_name]
    for name, text in old_assets.items():
        kind = name.rsplit('.', 1)[-1]
        if name in order or sum(n.endswith(kind) for n in order) >= KEEP_ASSETS:
            continue
        open(os.path.join(OUT, 'assets', name), 'w', encoding='utf-8').write(text)
        order.append(name)
    json.dump(order, open(os.path.join(OUT, 'assets', 'manifest.json'), 'w'), indent=1)

    for fname, src, bg, t_en, t_hy, desc in PAGES:
        view = os.path.splitext(fname)[0].replace('index', 'home')
        canonical = SITE_URL + '/' + ('' if fname == 'index.html' else fname)
        html = head(fname, t_en, t_hy, desc, canonical, css_name, js_name)
        if fname != 'index.html':
            html += home_link
        html += nav_lang
        html += f'<div class="view is-active" id="view-{view}">\n'
        html += '<div class="backdrop" aria-hidden="true"></div>\n'
        # every page closes on the seal, injected rather than pasted so the
        # pages cannot drift apart again
        page_body = body_of(src).replace('<footer>', '<footer>\n' + seal, 1)
        html += page_body + '\n</div>\n'
        html += lightbox + f'\n<script src="assets/{js_name}"></script>\n</body>\n</html>\n'
        open(os.path.join(OUT, fname), 'w', encoding='utf-8').write(html)


    for key in sorted(used) + [os.path.splitext(v)[0] for v in BACKDROP.values()]:
        shutil.copy(os.path.join(IMG, key + '.webp'), os.path.join(OUT, 'img', key + '.webp'))
    for fn in ['fraunces-600', 'fraunces-500i', 'ebgaramond-400', 'beaurivage',
               'noto-arm-400', 'manrope', 'noto-sans-arm']:
        src = os.path.join('fonts', fn + '.woff2')
        if not os.path.exists(src):
            open(src, 'wb').write(base64.b64decode(open('fonts/%s.b64' % fn).read().strip()))
        shutil.copy(src, os.path.join(OUT, 'fonts', fn + '.woff2'))

    if SITE_URL:
      urls = ''.join(
        f'  <url><loc>{SITE_URL}/{"" if f == "index.html" else f}</loc>'
          f'<changefreq>monthly</changefreq></url>\n' for f, *_ in PAGES)
      open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8').write(
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + '</urlset>\n')
    open(os.path.join(OUT, 'robots.txt'), 'w', encoding='utf-8').write(
        'User-agent: *\nDisallow: /\n' if not INDEXABLE else
        'User-agent: *\nAllow: /\n' + (f'Sitemap: {SITE_URL}/sitemap.xml\n' if SITE_URL else ''))
    open(os.path.join(OUT, '.nojekyll'), 'w').write('')

    # a wrong address should still land somewhere that looks like the archive
    nf = head('404.html', 'Not found — Nushik Malkhasyan', 'Չգտնվեց',
              'That page is not part of the archive.', SITE_URL + '/404.html',
              css_name, js_name)
    nf += home_link + nav_lang
    nf += ('<div class="view is-active" id="view-home">\n'
           '<div class="backdrop" aria-hidden="true"></div>\n'
           '<div class="page"><section class="hero">\n'
           '<h1 lang="hy">Չգտնվեց</h1>\n'
           '<p class="latin">Not found</p>\n'
           '<span class="rule" aria-hidden="true"></span>\n'
           '<p class="hero-sub i18n en is-visible">That page is not part of the archive. '
           'The four collections are gathered on the front page.</p>\n'
           '<p class="hero-sub i18n hy is-visible" lang="hy">Այդ էջը արխիվի մասը չէ։ '
           'Չորս ժողովածուն հավաքված են գլխավոր էջում։</p>\n'
           '<p class="cue is-visible"><a href="index.html" style="color:inherit">'
           '<span class="i18n en">Back to the archive</span>'
           '<span class="i18n hy" lang="hy">Վերադառնալ արխիվ</span></a></p>\n'
           '</section>\n')
    nf += '<footer>\n' + seal + '</footer>\n</div>\n'
    nf += f'<script src="assets/{js_name}"></script>\n</body>\n</html>\n'
    open(os.path.join(OUT, '404.html'), 'w', encoding='utf-8').write(nf)

    # Cloudflare Pages and Netlify both read this; GitHub Pages, where the site
    # lives today, ignores it and serves everything with max-age=600. The
    # stylesheet and script carry a content hash, so they can be cached
    # forever; the pages must not be. Because Pages will not honour that, the
    # last few hashed assets are kept on disk - see KEEP_ASSETS.
    open(os.path.join(OUT, '_headers'), 'w').write(
        '/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n\n'
        '/fonts/*\n  Cache-Control: public, max-age=31536000, immutable\n\n'
        '/img/*\n  Cache-Control: public, max-age=2592000\n\n'
        '/*.html\n  Cache-Control: public, max-age=0, must-revalidate\n')
    import make_icons
    make_icons.OUT = OUT
    open(os.path.join(OUT, 'favicon.svg'), 'w').write(make_icons.favicon_svg())
    make_icons.touch_icon(os.path.join(OUT, 'apple-touch-icon.png'))
    make_icons.share_card(os.path.join(OUT, 'img', 'share.jpg'))

    total = sum(os.path.getsize(os.path.join(r, f))
                for r, _, fs in os.walk(OUT) for f in fs)
    per = {}
    for fname, *_ in PAGES:
        page = open(os.path.join(OUT, fname), encoding='utf-8').read()
        imgs = set(re.findall(r'(?:src|data-zoom)="img/([^"]+)"', page))
        per[fname] = (os.path.getsize(os.path.join(OUT, fname))
                      + sum(os.path.getsize(os.path.join(OUT, 'img', i)) for i in imgs))
    print(f'dist/ total {total/1024/1024:.1f} MB, {len(used)} images')
    for f, b in per.items():
        print(f'  {f:14s} {b/1024/1024:5.1f} MB of images + html')


if __name__ == '__main__':
    main()

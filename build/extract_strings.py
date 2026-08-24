"""Pull every visible string out of the archive as English/Armenian pairs.

The pages carry both languages inline. The two are not always adjacent: some
blocks alternate en/hy, others list every English paragraph and then every
Armenian one. What holds in both is that within a given parent the two
languages appear in the same order, so they are zipped per parent rather than
matched by adjacency. A few strings exist in one language only - her name and
the place line are Armenian with a Latin gloss, alt text is English.
"""
import io, json, re
from bs4 import BeautifulSoup

PAGES = [
    ('Home', '_home_body.html'),
    ('Lace & Doilies', 'body2.html'),
    ('The Armenian Alphabet', 'template_alpha.html'),
    ('Lace to Wear', 'template_wear.html'),
    ('Crosses & Small Pieces', '_small_body.html'),
]

SECTION = {
    'hero': 'Hero', 'history': 'Essay', 'gallery': 'Gallery', 'collections': 'Collections',
    'about': 'About the maker', 'plates': 'Plates', 'works': 'Works', 'story': 'Story',
}


def txt(el):
    # no separator: the source already carries the spaces around inline <span>s,
    # and adding one puts a gap before the punctuation that follows them
    return re.sub(r'\s+', ' ', el.get_text('')).strip() if el is not None else ''


def where(el):
    sec = None
    for p in el.parents:
        cls = p.get('class') or []
        if p.name == 'section':
            sec = next((SECTION.get(c, c.title()) for c in cls if c in SECTION), None)
            if sec:
                break
        if p.name == 'footer':
            sec = 'Footer'; break
        if p.name == 'nav' and 'siblings' in cls:
            sec = 'Links to other collections'; break
        if 'lang' in cls and p.name == 'div':
            sec = 'Language toggle'; break
    # the marked element is often a bare <span> inside the styled one, so the
    # parent's classes are what say whether this is a label, a caption, a note
    cls = ' '.join((el.get('class') or []) + (el.parent.get('class') or [] if el.parent else []))
    kind = ('Heading' if el.name in ('h1', 'h2', 'h3') else
            'Button' if el.name == 'button' else
            'Label' if any(k in cls for k in ('kicker', 'eyebrow', 'cue', 'count', 'go', 'num', 'estd')) else
            'Caption' if any(k in cls for k in ('title', 'caption', 'sib-title')) else
            'Note' if 'disclaimer' in cls else
            'Body')
    return sec or 'Page', kind


def units(el):
    """A block may hold several paragraphs; split so the two languages line up."""
    ps = el.find_all('p', recursive=True)
    return [txt(p) for p in ps if txt(p)] if ps else ([txt(el)] if txt(el) else [])


rows, claimed = [], set()
for page, path in PAGES:
    soup = BeautifulSoup(io.open(path, encoding='utf-8').read(), 'html.parser')
    marked = soup.select('.i18n')

    # group by parent, then zip the two languages in document order
    # dedupe by identity: BeautifulSoup compares tags by content, so the four
    # identical "Enter / Մուտք" spans would otherwise collapse into one
    parents, seen_par = [], set()
    for el in marked:
        if id(el.parent) not in seen_par:
            seen_par.add(id(el.parent))
            parents.append(el.parent)
    for par in parents:
        en = [c for c in par.find_all(recursive=False)
              if 'i18n' in (c.get('class') or []) and 'en' in (c.get('class') or [])]
        hy = [c for c in par.find_all(recursive=False)
              if 'i18n' in (c.get('class') or []) and 'hy' in (c.get('class') or [])]
        sec, kind = where(en[0] if en else hy[0]) if (en or hy) else ('Page', 'Body')
        for i in range(max(len(en), len(hy))):
            e = units(en[i]) if i < len(en) else []
            h = units(hy[i]) if i < len(hy) else []
            for j in range(max(len(e), len(h))):
                rows.append({'page': page, 'section': sec, 'kind': kind,
                             'en': e[j] if j < len(e) else '',
                             'hy': h[j] if j < len(h) else ''})
        for n in en + hy:
            claimed.add(id(n))
            for d in n.find_all(True):
                claimed.add(id(d))

    # the place line is Armenian with its Latin gloss tucked in a <small>
    for el in soup.select('.place'):
        small = el.find('small')
        gloss = txt(small)
        if small:
            small.extract()
        rows.append({'page': page, 'section': 'Footer', 'kind': 'Place line',
                     'en': gloss, 'hy': txt(el)})
        claimed.add(id(el))

    # Armenian with no English twin - her name, the section titles
    for el in soup.find_all(attrs={'lang': 'hy'}):
        if id(el) in claimed or not txt(el) or el.find_parent(class_='tape'):
            continue
        if any(id(p) in claimed for p in el.parents):
            continue
        sec, kind = where(el)
        # each page titles itself in Armenian with the Latin reading beneath;
        # they belong on one line for proofreading
        gloss = ''
        if el.name == 'h1':
            nxt = el.find_next_sibling(class_='latin')
            if nxt is not None:
                gloss = txt(nxt)
                claimed.add(id(nxt))
        rows.append({'page': page, 'section': sec, 'kind': kind, 'en': gloss, 'hy': txt(el)})
        claimed.add(id(el))
        for d in el.find_all(True):
            claimed.add(id(d))

    # the Latin transliteration under each Armemian title
    for el in soup.select('.latin'):
        if id(el) in claimed or not txt(el):
            continue
        sec, kind = where(el)
        rows.append({'page': page, 'section': sec, 'kind': 'Latin gloss',
                     'en': txt(el), 'hy': ''})

io.open('strings.json', 'w', encoding='utf-8').write(
    json.dumps(rows, ensure_ascii=False, indent=1))
print(f'{len(rows)} strings')
for page, _ in PAGES:
    r = [x for x in rows if x['page'] == page]
    both = sum(1 for x in r if x['en'] and x['hy'])
    print(f'  {page:26s} {len(r):3d} strings, {both:3d} paired, {len(r)-both:2d} single-language')

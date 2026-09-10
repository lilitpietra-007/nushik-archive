"""Turn the hero's "Scroll" into a cue that says what is below and goes there.

"Scroll" tells a visitor to move but not what they will find, so the pieces
themselves went undiscovered. Each page now names its own count and links
straight to the works, with a chevron that bobs so it reads as a control.
"""
import io, re

CUES = {
    # file                 anchor    English                    Armenian
    '_home_body.html':     ('collections', 'Four collections',      'Չորս ժողովածու'),
    'body2.html':          ('works',       'Eleven pieces below',   'Տասնմեկ գործ ներքևում'),
    'template_alpha.html': ('works',       'Two works below',       'Երկու գործ ներքևում'),
    'template_wear.html':  ('works',       'Five pieces below',     'Հինգ գործ ներքևում'),
    '_small_body.html':    ('works',       'Nine pieces below',     'Ինը գործ ներքևում'),
}
CHEVRON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
           'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
           'aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>')

for path, (anchor, en, hy) in CUES.items():
    s = io.open(path, encoding='utf-8').read()

    # the works need something to link to
    target = 'collections' if anchor == 'collections' else 'gallery'
    s = s.replace(f'<section class="{target}">', f'<section class="{target}" id="{anchor}">', 1)

    cue = (f'<p class="cue reveal"><a href="#{anchor}">'
           f'<span><span class="i18n en">{en}</span>'
           f'<span class="i18n hy" lang="hy">{hy}</span></span>'
           f'{CHEVRON}</a></p>')
    s, n = re.subn(r'<p class="cue reveal">.*?</p>', cue, s, count=1, flags=re.S)
    assert n == 1, f'no cue found in {path}'

    io.open(path, 'w', encoding='utf-8').write(s)
    print(f'{path:22s} -> #{anchor}  "{en}"')

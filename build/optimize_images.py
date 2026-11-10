"""Write an AVIF beside every WebP, and keep the ones that are worth keeping.

AVIF is usually a third smaller than WebP at the same visible quality, but not
always: on some of the lace cutouts it comes out larger, because the alpha
channel is nearly all edge and AVIF has no advantage there. So each image is
encoded both ways and the AVIF is kept only when it saves at least MIN_GAIN.
build_static.py then serves whichever exist, AVIF first, WebP as the fallback.

Everything here is a second lossy pass over files that were already encoded
once - the originals from the cutout pipeline are gone - so the quality is set
high enough that the thread structure survives. Checked at 2x zoom against the
WebP before these numbers were chosen.

Backdrops get a lower setting than the pieces: every page lays a 60% dark veil
over them, which hides the artefacts a photograph of lace would show.
"""
import io
import os
import sys
from PIL import Image

IMG = 'img'
MIN_GAIN = 0.10          # keep the AVIF only if it is this much smaller
Q_PIECE = 55             # the lace, the crosses, the collars, the zooms
Q_GROUND = 50            # the painted backdrops, which sit under the veil
# garden.webp and portrait.webp are kept in img/ but no page uses them
GROUNDS = {'cottage', 'meadow', 'valley', 'field', 'sky', 'nushik'}
GROUND_SM = 900          # phone copy: 900px on the SHORTER side
SPEED = 4                # slower than the default; this runs rarely

# The four images on the home page's collection cards. Each is also a gallery
# thumbnail on its own collection page, where it is shown several times larger,
# so they cannot simply be shrunk - the home page gets its own smaller copy.
# The card box tops out at 171x192 CSS pixels, so 440 on the longer side covers
# a 2x desktop screen and a 3x phone with room to spare.
CARDS = {'lace_rosette', 'alpha_lace_cut', 'wear_collar_crown', 'cross_d'}
CARD_LONG = 440
# Most of the weight of a cutout is its alpha channel, which barely responds to
# the quality setting - from 50 to 74 the WebP moves by two per cent. So the
# setting is chosen low: the card is shown at 171px, and what it costs in
# artefacts cannot be seen at that size, while a higher setting costs real
# bytes in the AVIF.
Q_CARD = 50


def encode_im(im, quality):
    buf = io.BytesIO()
    im.save(buf, 'AVIF', quality=quality, speed=SPEED)
    return buf.getvalue()


def encode(path, quality):
    im = Image.open(path)
    im.load()
    return encode_im(im, quality)


def small_grounds():
    """A phone-sized copy of each painted backdrop.

    They are drawn with background-size:cover behind a dark veil, so a phone
    was downloading a 1209x1610 painting to fill a 390px column. The small
    copy is served by a media query.

    It is sized on the shorter side, not the width. cover on a tall phone
    scales a landscape painting until its height fills the screen, so sizing
    by width left the garden at 900x604 and the browser stretched it to
    1260x844 - soft, even under the veil.
    """
    for name in sorted(GROUNDS):
        src = os.path.join(IMG, name + '.webp')
        if not os.path.exists(src):
            continue
        im = Image.open(src)
        im.load()
        short = min(im.width, im.height)
        if short <= GROUND_SM:
            continue
        k = GROUND_SM / short
        sm = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        sm.save(os.path.join(IMG, name + '_sm.webp'), 'WEBP', quality=72, method=6)
        buf = io.BytesIO()
        sm.save(buf, 'AVIF', quality=Q_GROUND, speed=SPEED)
        w = os.path.getsize(os.path.join(IMG, name + '_sm.webp'))
        if len(buf.getvalue()) <= w * (1 - MIN_GAIN):
            open(os.path.join(IMG, name + '_sm.avif'), 'wb').write(buf.getvalue())
        print(f'  {name}_sm  {sm.width}x{sm.height}  webp {w / 1024:.0f} KB  '
              f'avif {len(buf.getvalue()) / 1024:.0f} KB')


def cards():
    """A card-sized copy of each image the home page shows on a card.

    The home page was serving the full gallery thumbnails into a 171x192 box -
    five to seven times more pixels than the box can show, and most of the
    weight of the first page anyone sees. The AVIF for these is written by the
    main loop below, like any other file in img/.
    """
    for name in sorted(CARDS):
        src = os.path.join(IMG, name + '.webp')
        if not os.path.exists(src):
            print(f'  {name}: no such image, skipped')
            continue
        im = Image.open(src)
        im.load()
        long_side = max(im.width, im.height)
        if long_side <= CARD_LONG:
            continue
        k = CARD_LONG / long_side
        sm = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        out = os.path.join(IMG, name + '_card.webp')
        buf = io.BytesIO()
        sm.save(buf, 'WEBP', quality=Q_CARD, method=6)

        # A card copy is only worth a second file if it is clearly lighter than
        # the image it was cut down from. On wear_collar_crown it is not: that
        # thumbnail is already small and nearly all alpha, and re-encoding it
        # at 440px came out heavier than the original. Where that happens no
        # copy is written and build_static.py serves the original.
        best_new = min(len(buf.getvalue()), len(encode_im(sm, Q_CARD)))
        best_old = min(os.path.getsize(src), len(encode(src, quality_for(name))))
        if best_new > best_old * (1 - MIN_GAIN):
            for stale in (out, os.path.join(IMG, name + '_card.avif')):
                if os.path.exists(stale):
                    os.remove(stale)
            print(f'  {name}_card  not worth it '
                  f'({best_new / 1024:.0f} KB vs {best_old / 1024:.0f} KB), using the original')
            continue
        open(out, 'wb').write(buf.getvalue())
        print(f'  {name}_card  {im.width}x{im.height} -> {sm.width}x{sm.height}  '
              f'{best_old / 1024:.0f} -> {best_new / 1024:.0f} KB served')


def quality_for(name):
    """The setting a given file is encoded at.

    The derived copies carry their parent's setting: without this a backdrop's
    phone copy was re-encoded at the piece setting, because "valley_sm" is not
    the name of a backdrop.
    """
    if name.endswith('_card'):
        return Q_CARD
    stem = name[:-3] if name.endswith('_sm') else name
    return Q_GROUND if stem in GROUNDS else Q_PIECE


def main():
    force = '--force' in sys.argv
    small_grounds()
    cards()
    kept = dropped = skipped = 0
    before = after = 0
    for fn in sorted(os.listdir(IMG)):
        if not fn.endswith('.webp'):
            continue
        name = fn[:-5]
        webp = os.path.join(IMG, fn)
        avif = os.path.join(IMG, name + '.avif')
        w_size = os.path.getsize(webp)
        before += w_size

        if not force and os.path.exists(avif) \
                and os.path.getmtime(avif) >= os.path.getmtime(webp):
            after += min(w_size, os.path.getsize(avif))
            skipped += 1
            continue

        data = encode(webp, quality_for(name))
        if len(data) <= w_size * (1 - MIN_GAIN):
            open(avif, 'wb').write(data)
            kept += 1
            after += len(data)
            print(f'  {name:30} {w_size / 1024:6.0f} -> {len(data) / 1024:6.0f} KB')
        else:
            if os.path.exists(avif):
                os.remove(avif)      # a previous run kept one that no longer wins
            dropped += 1
            after += w_size

    print(f'\n{kept} avif kept, {dropped} not worth it, {skipped} already current')
    print(f'served bytes {before / 1024 / 1024:.2f} MB -> {after / 1024 / 1024:.2f} MB '
          f'({after / before * 100:.0f}%)')


if __name__ == '__main__':
    main()

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
GROUNDS = {'cottage', 'meadow', 'portrait', 'garden', 'valley', 'sky'}
GROUND_SM = 900          # phone copy: 900px on the SHORTER side
SPEED = 4                # slower than the default; this runs rarely


def encode(path, quality):
    im = Image.open(path)
    im.load()
    buf = io.BytesIO()
    im.save(buf, 'AVIF', quality=quality, speed=SPEED)
    return buf.getvalue()


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


def main():
    force = '--force' in sys.argv
    small_grounds()
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

        data = encode(webp, Q_GROUND if name in GROUNDS else Q_PIECE)
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

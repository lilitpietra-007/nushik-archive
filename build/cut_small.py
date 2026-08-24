"""Cut the nine small pieces out of their slate backdrop.

The pieces are cream thread on dark slate, and four of them carry gold thread.
Gold is dimmer than cream, so a plain luminance key eats it; the warm lower-right
corner of the slate is about the same hue as gold, so a plain warm key eats that.
Both problems fall to the same observation: thread has texture, slate does not.
"""
import glob, os
import numpy as np
from PIL import Image
from scipy import ndimage

SRC = '/root/.claude/uploads/071e6230-7bb5-5595-b4c7-2f954253917a'
OUT = 'img'

# One photograph carries a patch of specular glare on the scratched slate that is
# as bright and as textured as the lace itself, so no gate separates the two. The
# doily's own top edge starts at 0.25 of the frame, well clear of it.
TRIM_TOP = {'sm_round': 0.245}

PIECES = {
    '9900': 'sm_rosette',
    '9902': 'sm_wheel',
    '9903': 'sm_round',
    '9904': 'sm_star',
    '9905': 'sm_initials',
    '9906': 'cross_c',
    '9907': 'cross_a',
    '9908': 'cross_d',
    '9909': 'cross_b',
}


def cut(path, trim_top=0.0):
    im = Image.open(path).convert('RGB')
    im.thumbnail((1400, 1400), Image.LANCZOS)
    rgb = np.asarray(im).astype(np.float32)
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = 0.299 * R + 0.587 * G + 0.114 * B
    sat = rgb.max(2) - rgb.min(2)

    # local standard deviation: high on thread, near zero on smooth slate
    m = ndimage.uniform_filter(lum, 9)
    sd = np.sqrt(np.maximum(ndimage.uniform_filter(lum * lum, 9) - m * m, 0))
    # the slate carries a glare band whose local sd sits near 32; the lace runs
    # near 78, so the gate goes between them rather than just above flat slate
    textured = ndimage.binary_dilation(
        ndimage.binary_closing(sd > 46, np.ones((5, 5))), np.ones((5, 5)))

    cream = np.clip((lum - 148) / 82, 0, 1)
    cream[cream < 0.08] = 0
    cream *= textured

    body = ndimage.binary_closing(cream > 0.15, np.ones((9, 9)))
    # gold must be warm, saturated, *textured*, and hard against the cream body
    near = ndimage.binary_dilation(body, np.ones((9, 9)))
    gold = (R > B + 18) & (R >= G - 10) & (sat > 30) & (lum > 92) & textured & near

    a = np.maximum(cream, np.clip((lum - 92) / 60, 0, 1) * gold)
    # even the dimmest gold sits near luminance 190, so fading out everything
    # below 150 drops the last scratched-slate wisps and no real thread
    a *= np.clip((lum - 150) / 40, 0, 1)
    if trim_top:
        a[:int(trim_top * rgb.shape[0])] = 0

    # one last component pass on the alpha itself: whatever is not joined to the
    # piece is glare, a neighbour, or the warm corner
    solid = ndimage.binary_closing(a > 0.2, np.ones((7, 7)))
    lab, n = ndimage.label(solid)
    if n:
        sizes = ndimage.sum(solid, lab, range(1, n + 1))
        keep = lab == int(np.argmax(sizes)) + 1
        a = a * ndimage.binary_dilation(keep, np.ones((7, 7)))

    ys, xs = np.where(a > 0.06)
    if len(ys):
        pad = 8
        a = a[max(0, ys.min() - pad):ys.max() + pad, max(0, xs.min() - pad):xs.max() + pad]
        rgb = rgb[max(0, ys.min() - pad):ys.max() + pad, max(0, xs.min() - pad):xs.max() + pad]

    # push the thread's own colour up so it reads as cream, not grey
    out = np.clip(rgb * 1.16 + 14, 0, 255)
    return Image.fromarray(
        np.dstack([out, np.clip(a * 255, 0, 255)]).astype(np.uint8), 'RGBA')


rows = []
for num, name in PIECES.items():
    src = glob.glob(f'{SRC}/*IMG_{num}.jpeg')[0]
    img = cut(src, TRIM_TOP.get(name, 0.0))
    disp = img.copy(); disp.thumbnail((620, 620), Image.LANCZOS)
    zoom = img.copy(); zoom.thumbnail((1000, 1000), Image.LANCZOS)
    disp.save(f'{OUT}/{name}.webp', quality=82, method=6)
    zoom.save(f'{OUT}/{name}_zoom.webp', quality=76, method=6)
    rows.append((name, disp))
    print(f'{name:12s} {img.size}  {os.path.getsize(f"{OUT}/{name}.webp")//1024}KB'
          f' + {os.path.getsize(f"{OUT}/{name}_zoom.webp")//1024}KB')

C, W = 5, 250
sheet = Image.new('RGB', (W * C, W * 2), (24, 21, 16))
for i, (name, im) in enumerate(rows):
    t = im.copy(); t.thumbnail((W - 16, W - 16), Image.LANCZOS)
    sheet.paste(t, ((i % C) * W + (W - t.size[0]) // 2,
                    (i // C) * W + (W - t.size[1]) // 2), t)
sheet.save(f'{OUT}/_small_cut_check.jpg', quality=84)

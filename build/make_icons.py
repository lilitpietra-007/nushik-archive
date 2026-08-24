"""Favicon, touch icon and the social-share card.

A photograph of lace is unreadable at 16 pixels, so the favicon is an abstract
medallion drawn from the same geometry her rounds are built on: a centre, a ring,
and twelve points worked outward from it. The share card is the real thing - the
home doily over the painting the site uses as its ground.
"""
import math, os
from PIL import Image, ImageFilter

OUT = 'dist'
INK, CREAM = '#16130e', '#f2ece0'


def favicon_svg():
    pts = []
    for i in range(12):
        a = math.radians(i * 30 - 90)
        pts.append(f'<circle cx="{16 + 10.5 * math.cos(a):.2f}" '
                   f'cy="{16 + 10.5 * math.sin(a):.2f}" r="1.5"/>')
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        f'<rect width="32" height="32" rx="6" fill="{INK}"/>'
        f'<g fill="none" stroke="{CREAM}" stroke-width="1.3">'
        '<circle cx="16" cy="16" r="10.5"/><circle cx="16" cy="16" r="5.5"/>'
        '</g>'
        f'<g fill="{CREAM}">{"".join(pts)}<circle cx="16" cy="16" r="2.1"/></g>'
        '</svg>')


def touch_icon(path):
    n = 180
    im = Image.new('RGB', (n, n), INK)
    mark = Image.open('img/home_mark.webp').convert('RGBA')
    mark.thumbnail((int(n * 0.82), int(n * 0.82)), Image.LANCZOS)
    im.paste(mark, ((n - mark.width) // 2, (n - mark.height) // 2), mark)
    im.save(path)


def share_card(path):
    W, H = 1200, 630
    bg = Image.open('img/cottage.webp').convert('RGB')
    # cover-crop the painting to the card
    s = max(W / bg.width, H / bg.height)
    bg = bg.resize((round(bg.width * s), round(bg.height * s)), Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, int((bg.height - H) * 0.42),
                  (bg.width - W) // 2 + W, int((bg.height - H) * 0.42) + H))
    veil = Image.new('RGB', (W, H), (10, 9, 6))
    bg = Image.blend(bg, veil, 0.55)
    mark = Image.open('img/home_mark.webp').convert('RGBA')
    mark.thumbnail((430, 430), Image.LANCZOS)
    glow = Image.new('RGBA', bg.size, (0, 0, 0, 0))
    glow.paste(mark, ((W - mark.width) // 2, (H - mark.height) // 2), mark)
    bg = Image.alpha_composite(bg.convert('RGBA'),
                               glow.filter(ImageFilter.GaussianBlur(18))).convert('RGB')
    bg.paste(mark, ((W - mark.width) // 2, (H - mark.height) // 2), mark)
    bg.save(path, quality=86, optimize=True)


if __name__ == '__main__':
    open(os.path.join(OUT, 'favicon.svg'), 'w').write(favicon_svg())
    touch_icon(os.path.join(OUT, 'apple-touch-icon.png'))
    share_card(os.path.join(OUT, 'img', 'share.jpg'))
    for f in ['favicon.svg', 'apple-touch-icon.png', 'img/share.jpg']:
        print(f'{f:22s} {os.path.getsize(os.path.join(OUT, f)) // 1024} KB')

"""Draw the lace rosette seal as SVG.

The mark is six-fold: a flower at the centre, a ring of pointed petals, six
large ogee petals each carrying a leaf sprig, and a small picot floret at every
outer point. Drawing it rather than tracing a bitmap keeps it a few kilobytes,
crisp at any size, and recolourable from CSS - the strokes inherit currentColor
so the same file works on the light ground and the dark one.
"""
import math

C = 100.0          # centre of a 200x200 viewBox
OUT = 'seal.svg'


def petal(r0, r1, w, k=0.42):
    """A pointed leaf from radius r0 out to r1, w wide, drawn pointing up."""
    b0, b1 = r0 + (r1 - r0) * k, r1 - (r1 - r0) * k
    return (f'M 0,{-r0:.1f} '
            f'C {w:.1f},{-b0:.1f} {w:.1f},{-b1:.1f} 0,{-r1:.1f} '
            f'C {-w:.1f},{-b1:.1f} {-w:.1f},{-b0:.1f} 0,{-r0:.1f} Z')


def ogee(r0, r1, w):
    """The onion-dome outline of the big outer petals: broad shoulders and a
    soft crown rather than a spike, which is what makes it read as lace."""
    return (f'M 0,{-r0:.1f} '
            f'C {w:.1f},{-r0 - 2:.1f} {w * 1.06:.1f},{-r1 + 26:.1f} '
            f'{w * 0.34:.1f},{-r1 + 3:.1f} '
            f'Q 0,{-r1 - 3:.1f} {-w * 0.34:.1f},{-r1 + 3:.1f} '
            f'C {-w * 1.06:.1f},{-r1 + 26:.1f} {-w:.1f},{-r0 - 2:.1f} 0,{-r0:.1f} Z')


def sprig(r, s=1.9):
    """Three leaves on a short stem - the filler inside each big petal. Wide
    and well separated, or at this size it reads as a chain rather than foliage."""
    p = [f'M 0,{-r + 5.5 * s:.1f} L 0,{-r - 6.5 * s:.1f}',
         f'M 0,{-r - 6.5 * s:.1f} m -1.6,0 a 1.6,1.6 0 1,0 3.2,0 a 1.6,1.6 0 1,0 -3.2,0']
    for dy in (4.0, -4.0):
        y = -r + dy * s
        for sx in (1, -1):
            p.append(f'M 0,{y:.1f} '
                     f'C {sx * 4.3 * s:.1f},{y - 0.4 * s:.1f} '
                     f'{sx * 4.1 * s:.1f},{y - 3.4 * s:.1f} '
                     f'{sx * 0.6 * s:.1f},{y - 4.2 * s:.1f} '
                     f'C {sx * 1.3 * s:.1f},{y - 2.2 * s:.1f} {sx * 1.0 * s:.1f},{y - 0.9 * s:.1f} 0,{y:.1f} Z')
    return ' '.join(p)


def floret(r, rad=5.0, dots=10, dotr=1.35):
    """A small ring encircled by picot dots, sitting at each outer point."""
    out = [f'<circle cx="0" cy="{-r:.1f}" r="{rad:.1f}"/>',
           f'<circle cx="0" cy="{-r:.1f}" r="{rad * 0.42:.1f}" class="dot"/>']
    ring = rad + dotr + 1.3
    for i in range(dots):
        a = 2 * math.pi * i / dots
        out.append(f'<circle cx="{math.sin(a) * ring:.2f}" '
                   f'cy="{-r - math.cos(a) * ring:.2f}" r="{dotr}" class="dot"/>')
    return ''.join(out)


wedge = [
    f'<path d="{ogee(36, 82, 30)}"/>',                 # big outer petal
    f'<path d="{petal(39, 72, 16)}"/>',                # its inner echo
    f'<path d="{sprig(56)}" class="leaf"/>',           # leaf sprig inside it
    f'<path d="{petal(14, 36, 9)}"/>',                 # inner ring petal
    floret(85),                                        # picot floret at the point
]
# the smaller petals sit between the big ones, so they get their own offset ring
between = [
    f'<path d="{petal(28, 60, 17)}"/>',
    f'<path d="{petal(12, 28, 7)}"/>',
]

parts = []
for i in range(6):
    a = i * 60
    parts.append(f'<g transform="rotate({a})">{"".join(wedge)}</g>')
    parts.append(f'<g transform="rotate({a + 30})">{"".join(between)}</g>')

# the flower at the middle
core = ['<circle cx="0" cy="0" r="3.1"/>', '<circle cx="0" cy="0" r="6.4"/>']
for i in range(12):
    core.append(f'<g transform="rotate({i * 30})"><path d="{petal(6.4, 11.6, 3.0)}"/></g>')
parts.append(''.join(core))

svg = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" '
    'fill="none" stroke="currentColor" stroke-width="1.15" '
    'stroke-linejoin="round" stroke-linecap="round" role="presentation">'
    '<style>.dot{fill:currentColor;stroke:none}'
    '.leaf{stroke-width:.9}</style>'
    f'<g transform="translate({C},{C})">{"".join(parts)}</g>'
    '</svg>'
)
open(OUT, 'w').write(svg)
print(f'{OUT}  {len(svg)} bytes')

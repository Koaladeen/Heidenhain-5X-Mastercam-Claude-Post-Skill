#!/usr/bin/env python3
"""Find the arc linearisation rule of a post from two Klartext programs of the same part.

    python arc_rules.py old.h new.h

Reads circle centre (CC X.. Y..) and arc blocks (C X.. Y.. DR+/-) together with the straight
moves (L ...) of both files and keys every arc by its start and end point. Arcs that exist in only
one file were written as straight L blocks by the other post. For both groups it prints radius,
chord, arc height (sagitta) and sweep angle, plus the extremes, so a clean threshold (e.g.
"sweep < 0.1 deg -> L") becomes visible. Test any rule on a second program before trusting it.
Only arcs in the XY plane with absolute CC/C coordinates are evaluated (no CR / CT / CP / incremental).
"""
import math
import re
import sys

BLOCK_NO = re.compile(r'^\s*\d+\s+')
WORD = re.compile(r'\b(I?[XYZ])([-+]?\d+\.?\d*)')


def arcs(path):
    x = y = None
    cx = cy = None
    out = []
    for raw in open(path, encoding='latin-1'):
        line = BLOCK_NO.sub('', raw.strip())
        if not line or line.startswith(';') or line.startswith('*'):
            continue
        w = {k: float(v) for k, v in WORD.findall(line)}
        if line.startswith('CC '):
            cx, cy = w.get('X', cx), w.get('Y', cy)
            continue
        if not (line.startswith('L ') or line.startswith('C ')):
            continue
        nx, ny = w.get('X', x), w.get('Y', y)
        if line.startswith('C ') and None not in (x, y, cx, cy):
            ccw = 'DR+' in line
            r = math.hypot(x - cx, y - cy)
            c = math.hypot(nx - x, ny - y)
            h = r - math.sqrt(max(r * r - (c / 2) ** 2, 0)) if c / 2 <= r else float('nan')
            d = math.degrees(math.atan2(ny - cy, nx - cx) - math.atan2(y - cy, x - cx))
            d = d % 360 if ccw else (-d) % 360
            out.append(((round(x, 3), round(y, 3), round(nx, 3), round(ny, 3)), r, c, h, d or 360.0))
        x, y = nx, ny
    return out


def show(title, rows):
    print('\n%s: %d' % (title, len(rows)))
    if not rows:
        return
    for key, label in ((1, 'radius'), (2, 'chord'), (3, 'height'), (4, 'sweep deg')):
        vals = [r[key] for r in rows if r[key] == r[key]]
        print('  %-10s min %.6f  max %.6f' % (label, min(vals), max(vals)))
    for r in sorted(rows, key=lambda r: r[4])[:8]:
        print('  R%.3f chord %.3f h %.6f sweep %.4f' % (r[1], r[2], r[3], r[4]))


def main():
    a, b = arcs(sys.argv[1]), arcs(sys.argv[2])
    ka, kb = {r[0] for r in a}, {r[0] for r in b}
    show('arcs in both files', [r for r in a if r[0] in kb])
    show('arcs only in %s (other post wrote L)' % sys.argv[1], [r for r in a if r[0] not in kb])
    show('arcs only in %s (other post wrote L)' % sys.argv[2], [r for r in b if r[0] not in ka])
    print('\nTip: compare the max sweep/height of an "only" group with the min of the "both" group.')


if __name__ == '__main__':
    main()

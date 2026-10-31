#!/usr/bin/env python3
"""Compare two Heidenhain Klartext programs (old post vs new post) and group the differences.

    python nc_diff.py old.h new.h [--ignore REGEX ...] [--show N] [--keep-numbers]

Leading block numbers are removed (they shift with every added line and would make every following
line differ), trailing spaces / CR are stripped, and lines matching --ignore are dropped before the
diff (defaults: time / date comment lines, BEGIN/END PGM lines). Every differing line is reduced to
a pattern with numbers replaced by '#', and the patterns are counted per side -
"257x < CYCL DEF 32.1 T#" tells you more than thousands of raw diff lines. The first N hunks are
printed as examples.
"""
import argparse
import difflib
import re
from collections import Counter

DEFAULT_IGNORE = [r'^;\s*(ZEIT|DATUM|UHRZEIT|TIME|DATE)\b', r'^(BEGIN|END) PGM ']
BLOCK_NO = re.compile(r'^\s*\d+\s+')


def read(path, ignore, keep_numbers=False):
    out = []
    for line in open(path, encoding='latin-1'):
        line = line.rstrip('\r\n').rstrip()
        if not keep_numbers:
            line = BLOCK_NO.sub('', line)
        if any(re.search(p, line) for p in ignore):
            continue
        out.append(line)
    return out


def pattern(line):
    return re.sub(r'[-+]?\d+\.?\d*', '#', line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('old')
    ap.add_argument('new')
    ap.add_argument('--ignore', action='append', default=[])
    ap.add_argument('--show', type=int, default=15, help='number of example hunks to print')
    ap.add_argument('--keep-numbers', action='store_true', help='do not strip block numbers')
    a = ap.parse_args()
    ign = DEFAULT_IGNORE + a.ignore
    o = read(a.old, ign, a.keep_numbers)
    n = read(a.new, ign, a.keep_numbers)
    sm = difflib.SequenceMatcher(None, o, n, autojunk=False)
    cnt = Counter()
    hunks = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        for l in o[i1:i2]:
            cnt['< ' + pattern(l)] += 1
        for l in n[j1:j2]:
            cnt['> ' + pattern(l)] += 1
        hunks.append((i1 + 1, j1 + 1, o[i1:i2], n[j1:j2]))
    print('%s: %d lines, %s: %d lines, %d differing hunks' % (a.old, len(o), a.new, len(n), len(hunks)))
    print('\nDifferences by pattern (< old only, > new only):')
    for k, v in cnt.most_common(60):
        print('%6d  %s' % (v, k))
    print('\nFirst %d hunks (line numbers after removing ignored lines):' % a.show)
    for i, j, ol, nl in hunks[:a.show]:
        print('--- old line %d / new line %d' % (i, j))
        for l in ol[:8]:
            print('< ' + l)
        for l in nl[:8]:
            print('> ' + l)


if __name__ == '__main__':
    main()

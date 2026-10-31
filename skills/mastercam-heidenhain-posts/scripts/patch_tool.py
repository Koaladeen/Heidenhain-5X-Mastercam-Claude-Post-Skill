#!/usr/bin/env python3
"""Helpers for building Mastercam MP posts from a base post with asserted text replacements.

Use as a library in a build script:

    from patch_tool import load, save, rep, replace_block
    t = load('base_post.pst')
    t = rep(t, 'old text\\n', 'new text\\n')                 # must occur exactly once
    t = replace_block(t, 'pfoo$  #start\\n', '#endregion\\n', 'pfoo$  #start\\n      ...\\n')
    save('my_post.pst', t)

or as a checker:

    python patch_tool.py --check my_post.pst

The checker reports line endings, duplicate postblock / variable definitions and identifiers that
are used in postblocks but never declared (heuristic: predefined engine names ending in '$' and
known functions are ignored - review the list, don't treat it as proof).
"""
import re
import sys


def load(path):
    """Read a post as text with LF line endings (posts are CRLF on disk)."""
    raw = open(path, 'rb').read().decode('latin-1')
    return raw.replace('\r\n', '\n')


def save(path, text):
    """Write LF text back as CRLF, latin-1 (MP posts are not UTF-8)."""
    open(path, 'wb').write(text.replace('\r\n', '\n').replace('\n', '\r\n').encode('latin-1'))


def rep(text, old, new, count=1):
    """Replace `old` by `new`; fail unless `old` occurs exactly `count` times."""
    n = text.count(old)
    if n != count:
        raise AssertionError('expected %d occurrence(s), found %d:\n%s' % (count, n, old[:200]))
    return text.replace(old, new)


def replace_block(text, start, end, new):
    """Replace from the line `start` up to (not including) the next `end` marker."""
    i = text.find(start)
    if i < 0 or text.count(start) != 1:
        raise AssertionError('block start not unique/found: ' + start[:120])
    j = text.find(end, i + len(start))
    if j < 0:
        raise AssertionError('block end not found after: ' + start[:120])
    return text[:i] + new + text[j:]


MP_FUNCTIONS = {
    'if', 'else', 'while', 'abs', 'int', 'frac', 'sqrt', 'sin', 'cos', 'tan', 'atan', 'atan2',
    'asin', 'acos', 'vequ', 'vsub', 'vadd', 'vscl', 'rotp', 'fmtrnd', 'force', 'unforce', 'newfs',
    'nwadrs', 'mprint', 'strstr', 'strlen', 'brksps', 'ucase', 'lcase', 'no2str', 'rpar',
    'rparsngl', 'fsg1', 'fsg2', 'fsg3', 'fsg4', 'and', 'or', 'not', 'result', 'e', 'n',
}


def check(path):
    raw = open(path, 'rb').read()
    crlf = raw.count(b'\r\n')
    lf = raw.count(b'\n') - crlf
    print('line endings: %d CRLF, %d bare LF%s' % (crlf, lf, '' if lf == 0 else '  <-- FIX'))
    text = raw.decode('latin-1').replace('\r\n', '\n')
    body = text.split('[CTRL_TEXT_XML_BEGIN]')[0]
    lines = body.split('\n')
    defs, blocks, vars_ = set(), [], []
    for l in lines:
        m = re.match(r'^([A-Za-z_][\w$]*)\s*:', l)
        if m:
            defs.add(m.group(1)); vars_.append(m.group(1))
        m = re.match(r'^fmt\s+"[^"]*"\s+\d+\s+([\w$]+)', l)
        if m:
            defs.add(m.group(1)); vars_.append(m.group(1))
        m = re.match(r'^fstrsel\s+\S+\s+\S+\s+(\S+)', l)
        if m:
            defs.add(m.group(1))
        m = re.match(r'^(p[\w$]*)(\s|$)', l)
        if m:
            defs.add(m.group(1)); blocks.append(m.group(1))
    from collections import Counter
    dup_b = [k for k, v in Counter(blocks).items() if v > 1]
    dup_v = [k for k, v in Counter(vars_).items() if v > 1 and not k.endswith('$')]
    print('duplicate postblocks:', dup_b or 'none')
    print('duplicate variables :', dup_v or 'none')
    used = set()
    for l in lines:
        if not l.startswith(' '):
            continue
        code = re.sub(r'"[^"]*"', '', l).split('#')[0]
        for w in re.findall(r'\b([A-Za-z_][\w]*)(\$?)', code):
            name = w[0] + w[1]
            if w[1] or name in MP_FUNCTIONS or name.startswith('prv_') or len(name) < 2:
                continue
            if re.match(r'^\d', name):
                continue
            used.add(name)
    undef = sorted(u for u in used if u not in defs)
    print('used but not declared (review):', undef or 'none')


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--check':
        check(sys.argv[2])
    else:
        print(__doc__)

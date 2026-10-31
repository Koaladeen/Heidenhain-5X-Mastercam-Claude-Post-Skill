#!/usr/bin/env python3
"""Deploy a post build to the live location without overwriting someone else's changes.

    python safe_deploy.py --live LIVE.pst --new BUILD.pst --expect MD5 --backup-dir DIR

1. Hash the live file. If it exists and its MD5 differs from --expect (the hash you recorded at
   the last deploy), stop: someone changed it - diff and merge first. Use --expect none for a
   first deploy to a location that has no file yet.
2. Copy the live file to DIR/<name>_<date>_<md5[:6]>.pst.
3. Copy the build over the live file, re-hash, compare with the build. Print the new hash - record
   it for the next deploy.
Only run this when the user asked for the deploy.
"""
import argparse
import datetime
import hashlib
import os
import shutil
import sys


def md5(path):
    return hashlib.md5(open(path, 'rb').read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--live', required=True)
    ap.add_argument('--new', required=True)
    ap.add_argument('--expect', required=True, help="MD5 of the live file from the last deploy, or 'none'")
    ap.add_argument('--backup-dir', required=True)
    a = ap.parse_args()
    if os.path.exists(a.live):
        live = md5(a.live)
        if a.expect != live:
            sys.exit('STOP: live file changed (md5 %s, expected %s) - diff and merge first, nothing copied.'
                     % (live, a.expect))
        os.makedirs(a.backup_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(a.live))[0]
        bak = os.path.join(a.backup_dir, '%s_%s_%s.pst' % (base, datetime.date.today().isoformat(), live[:6]))
        shutil.copy2(a.live, bak)
        print('backup :', bak)
    elif a.expect != 'none':
        sys.exit('STOP: live file does not exist but --expect is not none.')
    shutil.copyfile(a.new, a.live)
    new, built = md5(a.live), md5(a.new)
    if new != built:
        sys.exit('ERROR: copy verification failed (%s vs %s)' % (new, built))
    print('deployed:', a.live)
    print('md5     :', new, '(record this for the next deploy)')


if __name__ == '__main__':
    main()

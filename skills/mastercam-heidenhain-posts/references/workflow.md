# Workflow: building, testing and deploying posts

## Folder layout that worked

```
<post-project>/              # no spaces in folder or file names - Mastercam and some DNC tools choke
  work/
    base_post.pst            # untouched copy of the base post (CRLF)
    build_post.py            # base -> finished post, all changes as asserted replacements
    patch_*.py               # one script per feature, applied to build_post.py (optional)
    <post>.pst               # build output
    <post>_backup_<date>_before_<feature>.pst
  samples/                   # NC files from the old post (spec), screenshots, notes
  <post>.pst                 # copy of the current build for the user
```

The live post sits on the shared drive the CAM stations use. It is only ever replaced by an
explicit deploy step (`scripts/safe_deploy.py`).

## The build script

```python
from patch_tool import load, save, rep, replace_block
t = load('base_post.pst')                    # CRLF -> LF in memory
t = rep(t, 'old exact text\n', 'new text\n')            # must occur exactly once
t = rep(t, 'x\n', 'y\n', count=3)                        # or exactly 3 times
t = replace_block(t, 'pfoo$  #start line\n', '#endregion\n', 'new block\n')
save('my_post.pst', t)                       # LF -> CRLF
```

Why asserted replacements: the build fails loudly when the base text is not what you think,
instead of producing a post that silently lacks a feature. When a later feature changes text an
earlier replacement produced, patch the replacement text in the build script (or append a new
`rep` that works on the result) - both are fine as long as the build stays reproducible.

Add a **revision log** block at the top of the generated post (date, what, why, which sample
proved it). Update a **version line** setting (e.g. `spp_ver : "28-10-26"`) on every change and
print it in the NC header together with the post name - it answers "which post wrote this file?"
instantly.

## Settings block

Put everything a shop might tweak in one block near the top, with comments in the shop's language:
machine name, park positions, M-codes that differ per machine, dwell times, feature switches
(e.g. tool pre-selection on/off, park-and-TURN mode, probe tool number), defaults for dialog fields left at 0. Rules:
- one setting per line, comment says unit and meaning of 0,
- never read a setting directly in an output line - copy to a fmt variable (see mp-language.md),
- when a feature replaces old behaviour, keep a switch with the old behaviour available.

## Backups

- Before every build-script change: copy the build script with a dated suffix.
- Before every deploy: copy the live file into the backup folder with date and the first 6 hash
  characters (`<post>_2026-10-28_c16180.pst`).
- Never delete backups during a project.

## Deploy (only when the user says so)

1. Hash the live file. Compare with the hash you recorded at the last deploy.
2. Different? Someone changed it (a colleague, the control definition manager writing the text
   section, another session). Stop, diff, merge the change into the build script, rebuild.
3. Same? Back up the live file, copy the new build, hash again and compare with the build.
4. A copy can fail with "device or resource busy" while Mastercam has the post open - retry, never
   work around permission problems.
5. Tell the user the new hash, the backup file name, and what changed in NC terms.
6. A posting started within a second or two of the copy may still use the old file - check the
   header version line before analysing output.

## Testing loop

1. User posts a program with the old post -> `X-old.nc`, with the new post -> `X-new.nc`
   (Mastercam overwrites the NC file each time - insist on distinct names).
2. `python scripts/nc_diff.py X-old.nc X-new.nc` - grouped differences.
3. Classify each group: intended change / bug / data difference (operation settings that differ,
   e.g. coolant list entries) / rounding.
4. Fix bugs, rebuild, ask for a repost. Keep a list of intended differences so they are not
   re-investigated.
5. For logic that cannot be compared (new features), check the program in the TNC test run
   graphics, then dry-run on the machine with Z backed off.

## Several machines from one post

When a shop has similar machines, build them from one master build with per-machine settings
(name, probe tool, park positions, kinematics switch) rather than maintaining copies by hand.
Every code change goes to every derived post; only settings differ. Keep a small script that
generates each variant and verify all of them build after a change.

## Documentation for the shop

A short page per post: settings table, misc integer/real meanings, canned text entries, drill
cycle slot table, coolant list, what is checked (popups/stops), known limits. Update it with each
deploy - operators trust the page, not the code.

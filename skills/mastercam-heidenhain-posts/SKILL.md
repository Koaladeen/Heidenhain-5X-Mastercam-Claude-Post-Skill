---
name: mastercam-heidenhain-posts
description: Build, modify, debug and verify Mastercam MP post processors (.pst) for Heidenhain TNC controls (Klartext / conversational, TNC 530 / 620 / 640) - 3-axis, 3+2 with PLANE SPATIAL, 5-axis TCPM, CYCL DEF drill cycles, TCH PROBE probing through custom drill cycles, Q/QR parameters, serial number engraving, tool call / brake / coolant logic - and clone the behaviour of an existing or encrypted vendor post by comparing the .h output line by line. Use this skill whenever the user works on a Mastercam post for a Heidenhain machine, mentions the MP language, postblocks, NCI codes, misc integers/reals, canned text, control or machine definitions, posting errors (.err files, PST LINE errors), or wants Mastercam to produce different Heidenhain output - even if they never say "post processor".
---

# Mastercam MP posts for Heidenhain TNC

This skill captures field experience from building in-house Mastercam posts that replaced
encrypted vendor posts on Heidenhain TNC 530 / TNC 640 machines (5-axis A/C and B/C tables, and
3-axis machines generated from the same master post). It is about *how to work* on posts safely
and *what the traps are* - not a copy of Mastercam's or Heidenhain's documentation. When the user
has their own MP reference or cycle manual, those win over anything written here.

## Ground rules (read first)

These exist because a post bug becomes a crashed spindle, not a stack trace.

1. **Never edit the live post directly.** Posts usually live on a shared drive that the CAM
   stations read. Work on a local copy, keep a dated backup of every version you replace, and
   deploy only when the user explicitly says so. Before copying, hash the live file and compare it
   with the last version you deployed - if it changed, someone else (or Mastercam's control
   definition manager, which rewrites the text section) edited it: merge, never overwrite.
   `scripts/safe_deploy.py` does check -> backup -> copy -> verify.
2. **Build, don't hand-edit.** Generate the post from a base post (e.g. a generic post that ships
   with Mastercam, which the user is licensed to use) with a patch script that replaces exact text
   blocks and asserts each replacement matched the expected number of times. Re-running the script
   rebuilds the whole post, every change is reviewable, and a failed assert tells you immediately
   that the base text is not what you assumed. `scripts/patch_tool.py` has the helpers.
3. **Keep CRLF.** .pst files are CRLF. Python with binary read/write keeps them; `sed -i` and many
   editors silently convert. Check with `file x.pst` after every write.
4. **Respect other people's IP.** Never decrypt, decode or disassemble encrypted posts (.psb or
   other vendor-protected formats). Their *NC output* is fair game as a specification: post the
   same part with the old post and match the output. Don't paste large chunks of Mastercam's
   generic posts or documentation into anything the user wants to publish.
5. **Verify with NC files, not with intuition.** "It builds" means nothing. The proof is: the user
   posts a real program with the new post and you diff it against the old post's output, category
   by category (see `references/matching-old-posts.md`). New features get a check in the TNC's
   test run / graphics and a dry run on the machine before cutting.
6. **Ask about machine facts, never guess them.** Brake M-codes, coolant codes, rotary travel,
   preferred PLANE mode (STAY / TURN / SEQ), probe tool number, which Q / QR parameters are free.
   If the user doesn't know, build it as a setting with a clearly marked default.

## Typical workflow

1. **Collect the spec.** Sample `.h` programs from the old post (the more operation types the
   better), screenshots of planes / misc value dialogs / coolant lists / drill cycle lists, and a
   short text with what the shop wants changed. Note every machine fact in one place.
2. **Pick a base post** and copy it into a work folder. Never modify the original.
3. **Write the build script**: header/revision log, a settings block at the top of the post (names
   in the shop's language are fine), then one replacement per feature. Keep a changelog in the
   post's revision log - future you needs the "why".
4. **Static check** after each build: undefined identifiers, duplicate variable / postblock
   definitions, CRLF (`scripts/patch_tool.py --check`).
5. **User posts, you diff** (`scripts/nc_diff.py old.h new.h` - it ignores the block numbers that
   shift with every added line). Fix real differences, document deliberate ones. Repeat until only
   intended differences remain.
6. **Deploy only on request**, with hash check and backup, then tell the user exactly which file
   changed, the hash, and where the backup is.

## Which reference to read

| Situation | Read |
|---|---|
| Writing or patching MP code, posting errors, strange output | `references/mp-language.md` |
| Build scripts, backups, deploy, settings block, revision log | `references/workflow.md` |
| Cloning an old/encrypted post from its NC output, diff categories, deriving hidden rules | `references/matching-old-posts.md` |
| Program frame, TOOL CALL, CYCL 32, PLANE SPATIAL, datum shifts, TCPM, LN radius comp, brakes, extras | `references/heidenhain-tnc.md` |
| CYCL DEF drill cycles, custom cycle slots, TCH PROBE through custom cycles, dialog labels | `references/drill-and-probe-cycles.md` |
| Serial numbers with a QR counter and a built-in single-stroke font | `references/serial-engraving.md` |
| NCI codes, tool changes, operations, parameter numbers, tool plane matrix | `references/nci-and-parameters.md` |

## The ten traps that cost the most time

Details and fixes are in `references/mp-language.md` and `references/heidenhain-tnc.md`.

1. `no2str()` is only allowed in a string assignment, never inside an output line (PST LINE error
   94). Build the string first, then output it.
2. A one-line `else, statement` belongs to the statement directly before it; nest with brackets.
   Write multi-statement branches out as blocks.
3. A bare `e$` (empty block) is dropped. For a visually empty line output a one-space string.
4. Variables declared with `fmt` are output variables; keep machine settings in separate plain
   variables and copy them into the fmt variable right before output.
5. The engine resolves a single rotary axis (`c$`) for every operation as soon as the post reads
   `c$`, and logs "only single axis rotation allowed" (localised, e.g. German "Nur
   Einzel-Achsenrotation zulässig") on compound planes. Remove every `c$` read and set
   `rotaxtyp$ = 3` - also again after every `rd_md$`, which resets it.
6. With that rotary setup, Mastercam does not always send the "real tool change" call (gcode 1002)
   after multiaxis operations. Track your own "tool active" flag and write the tool end yourself -
   otherwise TCPM stays on and the next operation's radius compensation fails.
7. Mastercam sends null tool changes (gcode 1000) *inside* one operation (depth passes, transform
   instances, multi-pass). Decide what to output from what actually changed (plane, datum, spindle,
   coolant), not from the operation id alone.
8. `tox$/toy$/toz$` are the plane origin in **plane** coordinates. For a `CYCL DEF 7` datum shift in
   the Top frame convert with the plane matrix rows first.
9. Re-setup checks must compare with a tolerance (`abs() > 0.0005`), not exact equality - floating
   point noise otherwise forces a full PLANE re-setup on every operation of the same plane.
10. Mastercam's NC output folder holds only the last posting. Ask the user to save comparison
    files under distinct names (`-old.h` / `-new.h`) - and print the post name and version in the
    header so you can see which post actually produced a file.

## Scripts

All scripts are plain Python 3 without dependencies.

- `scripts/patch_tool.py` - `rep()` / `replace_block()` with exact-count asserts, CRLF-safe
  read/write, and `--check` (undefined identifiers, duplicate definitions, line endings).
- `scripts/nc_diff.py old.h new.h` - removes Klartext block numbers and time/date lines, diffs, and
  groups the differences by pattern (numbers replaced by `#`), so you see "257x < CYCL DEF 32.1"
  instead of thousands of shifted lines.
- `scripts/arc_rules.py old.h new.h` - finds arcs (`CC` + `C`) one post wrote as `L` and the other
  as an arc, and prints radius, chord, arc height and sweep angle so the hidden linearisation rule
  becomes visible.
- `scripts/safe_deploy.py --live L --new N --expect HASH --backup-dir D` - refuses to overwrite a
  live file that changed since the last deploy, backs it up, copies, verifies.

`assets/stroke_font.json` is a single-stroke font (A-Z, 0-9, `- / .`) in a 0.6 x 1 unit cell, made
for engraving with cutting tools. Format and usage: `references/serial-engraving.md`.

## Talking to the user

Shop users are machinists and programmers, not software people. Show NC blocks, not variable
names, when explaining output. When you change behaviour, show the before/after blocks. Mark
clearly what is verified (posted and compared, or run on the machine) versus only built.

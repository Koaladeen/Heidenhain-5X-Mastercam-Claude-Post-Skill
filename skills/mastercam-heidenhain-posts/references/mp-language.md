# MP language - practical notes and traps

Field notes from writing and patching real posts. Names of predefined postblocks and variables
(`psof$`, `ptlchg0$`, `x$`, `mi1$` ...) are Mastercam's API; check the user's MP reference for the
full list. Everything here was observed in practice - if your post behaves differently, believe
the post and the NC file.

## Contents
1. Output lines and modality
2. Formats (fs2 / fmt)
3. Strings
4. Control flow
5. Postblock call order and what is valid where
6. Engine traps (rotary, tool change, next tool, feed)
7. Debugging techniques
8. Error messages

## 1. Output lines and modality

- An output line is a comma separated list ending with `e$`. `n$` writes the sequence number
  (suppressed with `omitseq$ = yes$`).
- Prefixes on a variable: `*var` forces output, `!var` updates the "previous" value without output,
  `` `var `` (backtick) updates without forcing. Plain `var` is modal: written only when the
  formatted value differs from `prv_var`.
- Conditional output inside a line: `[if gcode$, *feed]`. Works for strings too:
  `[if tcpm_on = zero, " FUNCTION TCPM F TCP AXIS POS PATHCTRL AXIS"]`.
- To force the next modal output of a variable, set its previous value to a sentinel:
  `prv_xabs = c9k` (c9k is a large constant in the generic posts). `result = force(a, b)` exists
  but forcing with several arguments was unreliable for one of them in practice - set `prv_` values
  explicitly when it matters.
- `result = newfs(n, var)` switches a variable to another format **and forces its next output**.
  Generic posts call it at every tool change / null tool change for `feed`, which re-outputs F after
  every depth pass. Remove those calls if the target control keeps F modal.
- A **bare `e$`** (nothing written) is dropped - no empty line. Write a one-space string variable
  (`sblank_ln : " "` then `sblank_ln, e$`) for a visually empty line.
- `spaces$` controls spaces between words. With `spaces$ = one` you get `L X+1 Y+2 FMAX`.
  Strings are written as they are, so with spaces on, `"Q1701 = ", *var` may get an extra space.
  For lines that need exact spacing set `spaces$ = zero` around the block and add spaces yourself;
  restore afterwards. Klartext needs a space after the block number and between words.
- A **single-quoted** literal in an output line is silently dropped. Use double quotes.
- One Q parameter assignment per block (`FN 0: Q1 = +5`, `Q2 = Q1 * 2`), one comment per block, and
  a comment must end the block.

## 2. Formats (fs2 / fmt)

- `fs2 n a.b c.d[flags]` - first pair inch, second metric. Flags used in practice:
  `l` = leading zero(s) (with `1.4 1.3l` you get `0.2` instead of `.2`), `t` = trailing zeros,
  `d` = delta/incremental, `n` = always output.
- `^` instead of `.` (`fs2 23 0^3 0^3`) omits the decimal point for whole numbers (`F4350`,
  `F2238.075`). It also drops a `+` sign - for Heidenhain `X+12.5` style, give the sign through the
  fmt prefix or a second format.
- `fmt "X" 2 xabs` binds prefix, format number and variable. The prefix may contain spaces and
  symbols (`fmt " CYCL DEF 7.1 IX" 2 v`, `fmt " Q1710 = INT ( Q1701 / " 4 v`, `fmt " LBL " 4 v`).
  A fmt without prefix (`fmt 4 v`) works too.
- Integer formats (e.g. `fs2 4 1 0 1 0`) are not limited to one digit; `N92001` works.
- `fmtrnd(v)` rounds with the variable's format; for unformatted variables it uses 7 decimals -
  compare floats with `abs(a - b) < tol` instead of `fmtrnd(a) = fmtrnd(b)` in that case.
- Keep **settings** (values the user edits at the top of the post) in plain variables and copy them
  into fmt variables right before output. Mixing both made settings change format or vanish from
  modal checks.

## 3. Strings

- `no2str(x)` only in a **string assignment**: `s = "OP " + no2str(op_id$)`. Inside an output line
  it fails with PST LINE error 94.
- `no2str(0.5)` gives `.5` (no leading zero) and `no2str(4)` gives `4.` - use fmt variables for
  numbers that end up in NC code.
- Useful functions: `strlen(s)`, `strstr(needle, haystack)` (position, 0 = not found),
  `brksps(pos, s)` (splits: returns the rest from pos, `s` keeps the head), `ucase(s)`.
- Loop over characters: `rest = brksps(two, tmp)` leaves the first character in `tmp`.
- Comments from the operation arrive in `pcomment$` with `scomm$`; `gcode$` tells the type
  (1005/1006/1007/1026 manual entries, 1008 operation comment).

## 4. Control flow

- `if cond, statement` and `else, statement` - the `else` binds to the immediately preceding `if`
  line. For more than one statement use brackets on their own lines:
  ```
  if a > zero,
    [
    b = one
    c = two
    ]
  else,
    [
    b = zero
    ]
  ```
- `while cond, [ ... ]` exists - always add a loop guard counter.
- Several assignments plus a postblock call on one line work: `ser_u = 0.3, ser_v = 1, pser_r`.
- Constants `zero` .. `six`, `m_one` exist in the generic posts; **`seven` does not** - write 7.
- Engine functions cannot always be nested inside an `if` comparison (e.g. `rparsngl`); assign to a
  variable first.
- Trig functions use degrees (`sin`, `cos`, `atan2(y, x)`); `^` is power; `int()` truncates.
- There is no "return": structure postblocks so the decision happens in the caller
  (`if s4x, p4x_start` / `else, pb_calc3`).

## 5. Postblock call order and what is valid where

- `pprep$` runs before the NC file is open - no output there (reading machine/control definition is fine).
- `pq$` runs once before processing - good place for `spaces$`, `omitseq$`, `stagetool`, `bldnxtool$`.
- `pheader$` before the first tool, `psof$` start of file (first tool), `ptlchg$` real tool change,
  `ptlchg0$` null tool change (same tool, new operation or a break inside an operation),
  `ptlchg1002$` is called around real tool changes and is a good place to detect a new operation
  (`op_id$ <> prv_op_id$`) and clear per-operation state.
- `pretract` (generic posts) is the tool end; `peof$` end of file.
- `pwrtt$` is the pre-read (needs `tooltable$` set) - count tools, collect tool numbers, check
  duplicates, before any output happens.
- `pparameter$` receives operation parameters (`prmcode$` / `sparameter$`, read with `rpar`).
  `pmachineinfo$` receives machine / control definition values after `rd_md$` / `rd_cd$`.
- Motion: `prapid$`, `plin$`, `pcir$`, `pmx$` (vector / multiaxis lines) - in the generic posts all
  funnel into one motion output postblock; that is the single place to hook alternative output
  (TCPM, LN vectors, engraving).
- Drill: `pdrill$`, `ppeck$`, `pchpbrk$`, `ptap$`, `pbore1$`, `pbore2$`, `pmisc1$`, `pmisc2$`,
  `pdrlcst$` (custom) for the first hole, the same names with `_2$` for following holes,
  `pcanceldc$` at the end.

## 6. Engine traps

**Rotary resolution warning.** On machines where planes are compound rotations (A/C or B/C tables,
or rotary tables with planes defined around a world axis), the engine logs "only single axis rotation
allowed" per operation (`.err`, localised text). Cause: the engine resolves a single rotary angle
whenever the post reads `c$`. Fix that worked on A/C and B/C machines:
1. remove every read of `c$` (generic posts read it in the coordinate mapping postblocks),
2. set `rotaxtyp$ = 3` in the declaration, in `pprep$` after `rd_md$`, and right after every
   `rd_md$` in the machine-read postblock (the read resets it to 1),
3. declare the machine base matrix (`matb1$..matb9$` = identity for Top) and generous rotary limits.
Things that did **not** help: `err_file$`, the `[POST_VERSION]` flags, `rotary_axis$`.

**Missing tool end after rotary setup.** With the setup above, the 1002 call before a real tool
change sometimes doesn't come. Keep `tl_active` (set when the tool change is written, cleared in
the tool end) and in `ptlchg$` call the tool end first if `tl_active` is still set. Guard the
normal 1002 path with the same flag so it is never written twice.

**Null tool changes.** gcode 1000 arrives at operation changes and also inside one operation. Do not
rely on `op_id$`. Decide from state: work offset values changed? B / plane changed? spindle /
coolant changed? Only then write the operation change block. Transform instances share the
operation id but have different plane origins.

**Next tool.** `next_tool$` is only filled when `bldnxtool$` is on (control definition switch).
Set `bldnxtool$ = one` in `pq$`. `ntools$` may also be 1 - count tools in `pwrtt$` yourself
(`if t$ > zero & gcode$ <> 1003 & t$ <> last, count = count + one`). At the last tool, the shop
usually wants the first tool staged (`first_tool$`).

**Feed modality.** Besides `newfs()`, generic posts force feed after rapids (a `force_feed`
switch) and compute feed in the coordinate mapping postblock on every move (also rapids). If the
old post kept F modal after `FMAX` moves, write F through your own postblock:
```
pfout
      if fmtrnd(feed) <> f_last, *feed
      f_last = fmtrnd(feed)
```
and reset `f_last = m_one` where F must appear again (tool change, after a drill cycle, after a
PLANE / TCPM change, after a probing cycle).

**Spindle changes.** On Heidenhain a speed change within a tool is `TOOL CALL S..` (or `TOOL CALL n Z
S..`). Compare with the old post. For probes write `S0` - otherwise the control keeps the previous
speed.

**Arcs.** Klartext arcs are `CC X.. Y..` (centre) plus `C X.. Y.. DR+/-`. Generic posts may drop the
unchanged axis; many shops expect both X and Y on every arc: output `*xabs, *yabs`. Helical arcs
can be written as `CP IPA.. Z.. DR..` - compute the angle from the *rounded* start/centre/end the
way the old post did (compare thousands of blocks, not three). Very small arcs: old posts often
linearise by **sweep angle** (`sweep$`, degrees) - find the threshold from data
(`scripts/arc_rules.py`), not by guessing radius or chord.

## 7. Debugging techniques

- **Parameter dump switch.** Add a setting (e.g. `prm_debug`) that writes every `prmcode$` and
  `sparameter$` of each operation as comments. Post once, search the dump for a value you typed into
  a dialog field - that is how unknown parameter numbers are found. Switch it off before deploying.
- **Trace comments.** Temporary `n$, "( DBG B=", *b_dbg, " )", e$` lines at decision points.
  Remove before deploy.
- **Static check** after each build: every identifier used in a postblock is declared, no
  duplicate postblock/variable names (MP accepts some duplicates silently - the second wins).
- The `.err` file next to the NC (or the post) logs runtime messages with operation ids.

## 8. Error messages

- `PST LINE n ... [94]` - function used where only a string assignment is allowed (`no2str` in an
  output line).
- Posting stops without a message - an `exitpost$` from your own checks; always pair it with
  `result = mprint(msg)` so the user knows why.
- "only single axis rotation allowed" in the `.err` - see section 6.
- Output identical after a change - the CAM station may still have the previous post loaded or the
  machine definition points to another post file. Check the post name line in the header.

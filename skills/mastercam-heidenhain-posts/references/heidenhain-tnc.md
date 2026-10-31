# Heidenhain TNC (Klartext) posts

Notes from posts for TNC 530 / TNC 640 on 5-axis machines with A/C and B/C tables, and a 3-axis
variant generated from the same master. Check every cycle number and Q parameter against the
machine's own cycle documentation - options differ between controls.

## Contents
1. Program frame and comments
2. Tool call, tolerance, tool pre-selection
3. Planes (3+2) and datum shifts
4. 5-axis (TCPM), radius compensation, linking
5. Brakes and rotary limits
6. Drilling and probing
7. Extras that shops liked
8. 3-axis variant

## 1. Program frame and comments

- `0 BEGIN PGM name MM` ... `END PGM name MM`, block numbers counting from 0 (set `n$` start and
  increment yourself if the control definition differs).
- Comment blocks: `; TEXT`. A comment must end the block, so give every comment type its own block.
- Structure lines (`* - TEXT`) show up in the TNC's structure view. Useful for the operation name,
  the tool, and an explicit `* - PROGRAMM ENDE` right before the end - with engraving routines after
  the main program the end is otherwise hard to find.
- Some TNCs accept only two M functions per block - split coolant / brake / spindle M-codes.
- `BLK FORM 0.1 Z X.. Y.. Z..` / `0.2` from the stock setup (toolpath group parameters) helps the
  operator's simulation.

## 2. Tool call, tolerance, pre-selection

- `TOOL CALL n Z Sxxxx` (DL/DR optionally from misc reals or Q parameters: `DL+Q10`).
- Probe tools: `TOOL CALL n Z S0` - otherwise the control keeps the previous speed, which can exceed
  the probe's limit. No M3, no coolant for the probe.
- `TOOL DEF next` pre-selection: switch it off for carousel magazines that cannot pre-stage.
- `CYCL DEF 32 TOLERANZ` per operation: T from the operation's chordal tolerance + filter
  tolerance (find the parameter numbers with a parameter dump; they differ per toolpath type and
  some multiaxis types pass none -> provide a misc real override). Guard against tiny values (a
  helix operation produced T0.003) with a minimum and default. TA (angle tolerance) only matters
  with TCPM. Optional: HSC mode from the operation type parameter (roughing vs finishing).

## 3. Planes (3+2) and datum shifts

- Tool plane matrix rows: `m1$..m3$` = plane X axis, `m4$..m6$` = Y, `m7$..m9$` = Z (tool axis),
  in world (Top) coordinates.
- `tox$/toy$/toz$` are the plane origin **in plane coordinates**. For a datum shift in the Top frame
  convert: world origin = tox*X + toy*Y + toz*Z (rows of the matrix).
- Sequence that worked: absolute `CYCL DEF 7` datum shift to the plane origin, then
  `PLANE SPATIAL SPA.. SPB.. SPC.. STAY` (or TURN), then position.
- `PLANE SPATIAL` angles: compute the machine solution yourself and write it in a form the control
  reproduces exactly. With an A/C table the vendor convention `SPA=A SPB=0 SPC=C` (machine angles)
  plus coordinates rotated into that frame worked; for B/C: `SPA=0 SPB=B SPC=C`.
- `STAY` + rotary axes in the first positioning block (`L X.. Y.. A.. C.. FMAX`) moves everything at
  once (shop favourite). `TURN` at a park position is a safer option for large parts - offer both
  as a setting and a per-operation misc integer.
- `M140 MB MAX` retract before turning; not needed on 3-axis machines.
- Datum table instead of explicit shifts: the plane's "work offset" field (a parameter, -1 = auto)
  can select `CYCL DEF 7.0 / 7.1 #n`.
- Fine corrections per plane via the plane comment (e.g. `X0.03 Y0 Z-0.02`) -> incremental
  `CYCL DEF 7` after the PLANE. Warn at the end of posting which operations got corrections (copied
  programs carry corrections for another machine). Compare re-setup conditions with a tolerance
  (`abs() > 0.0005`), not exact equality - floating point noise caused a re-setup on every
  operation.

## 4. 5-axis (TCPM), radius compensation, linking

- `FUNCTION TCPM F TCP AXIS POS PATHCTRL AXIS` (newer) or `M128` (older); `FUNCTION RESET TCPM` /
  `M129` at the end. Always reset at the tool end - a missing tool end (see 1002 trap) left TCPM
  active and broke the next operation's radius compensation.
- 5-axis tool radius compensation: `LN X Y Z NX NY NZ TX TY TZ RL/RR` with `PATHCTRL VECTOR`;
  NX/NY/NZ = surface normal from the NCI, TX/TY/TZ = tool vector. Restrict to tool plane Top.
- Choosing the rotary solution: within axis travel, prefer the shop's direction (SEQ) for the
  first point, then nearest solution. Stop posting with a clear message when a plane is outside
  travel.
- Multiaxis linking (link moves between operations): keep TCPM on through the link, release brakes
  once at the start of the linked group and clamp after the last operation. The last link point is
  the start of the next segment.
- Multiaxis drilling: per hole direction `PLANE SPATIAL ... STAY` + positioning + cycle, same
  direction -> just `L X Y M99`. In multiaxis drilling the engine gives depth/clearance values
  **incremental from the hole point** - compute Q203/Q200/Q201/Q204 from the drill points rotated
  into the plane instead.

## 5. Brakes and rotary limits

- Rotary brakes are machine M-codes (one pair per axis on some machines). Pattern that shops liked:
  canned text entry "release" sets a state that keeps brakes open (no clamp after positioning)
  until canned text "clamp". Without the state, clamp after every positioning and before 3+2 cuts.
- Write brake M-codes in their own block before the move.

## 6. Drilling and probing

- Cycles 200/201/203/205/207/209/208 etc. via `CYCL DEF` with commented Q parameters
  (`Q200=+2 ;SICHERHEITS-ABST.`), then `L X Y FMAX M99` per hole or `CYCL CALL`.
- Probing without a CAM probing licence: map TCH PROBE cycles (4xx datum cycles) onto unused custom
  drill cycles. See `drill-and-probe-cycles.md` for slot planning, field mapping and dialog labels.
- Datum value = programmed point of the "hole" (Q331/Q332), not zero.
- `TCH PROBE 441` (fast probing) after the probe tool call with the probe operation's feed; cap
  with the metric feed limit (the inch limit variable may still hold the default at the first tool).
- Tool measurement (`TCH PROBE 584`) and breakage check (`TCH PROBE 586`, on some machines with an
  M-code before it, but not for the last check of the program) via misc integers.

## 7. Extras that shops liked

- Header: machine, post name, post version (`; PP-STAND : dd-mm-yy`), tool list with stick-out
  (a tool parameter), optional ASCII banner (keep to `# + - |`, max ~31 characters wide).
- `; Z MAX / Z MIN` (and Y range on tilting machines) per operation, written **before** the
  operation: buffer the operation in an extra output stream with a reserved line, fill it at the
  operation end.
- Spindle run-up dwell (`CYCL DEF 9`) when the estimated rapid time from M3 to the first cut is
  shorter than the run-up time for the speed.
- Popups (warnings, not stops) for F0, S0, S above max, duplicate tool numbers, different presets.
- Run time estimate per tool and total.

## 8. 3-axis variant

Generate it from the 5-axis master with settings: no rotary output, no `M140`, end of program
`L Z+park F MAX M92` then the XY park line. Allow two probe tool numbers if the shop's 3-axis
machines differ, and stop posting when a probe number is used in a cutting operation.

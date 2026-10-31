# Drill cycles, custom cycle slots, probing

## Slot numbering

The operation's drill cycle list has 8 standard entries and 12 custom entries (cycles 9-20). In the
engine `drillcyc$` is **zero based**: list entry 1 -> 0, entry 9 (first custom) -> 8, entry 15 -> 14.
Standard entries call their own postblocks (drill / peck / chip break / tap / bore 1 / bore 2 /
misc 1 / misc 2), custom entries call the custom postblock with `drillcyc$` 8..19. First hole and
following holes have separate postblocks (`..._2$`).

The *names* shown in the list come from the control definition and can be anything. A shop's old
post may have used its own order (e.g. entry 2 "Cycle 203", entry 5 "Cycle 201 reaming", entry 7
"Cycle 205", entry 8 "Cycle 241"). Existing jobs store the entry number, so a new post must keep the
old order or every old job posts the wrong cycle. Get one operation per entry posted with the old
post (in list order) and map them. Shops often use only a few cycles (count them in their program
archive) - the unused standard slots and the custom slots are then free for probing or engraving.

## Fields

Engine variables behind the dialog fields: `depth$`, `refht$` (retract/R plane), `initht$`
(clearance), `tosz$` (top of stock), `peck1$`, `peck2$`, `peckclr$`, `retr$` (retract amount),
`dwell$`, `shftdrl$` (shift), custom parameters `drl_prm1$..drl_prm10$`, feed `fr_pos$`.
Labels can be renamed per cycle in the control definition - a field labelled "clearance/shift"
may feed `peck1$`. Verify by entering distinct values (1, 2, 3 ...) and posting.

In normal (single plane) drilling these values are absolute in the tool plane. In **multiaxis
drilling** they are incremental from the hole point - compute absolute values from the drill point
vectors instead.

## Dialog labels from the post

The post's text section (control definition text, XML) can define descriptions and field labels
per cycle, e.g. elements `drill_cycle_9` (fields `clearance`, `retract`, `depth`, `first_peck`,
`subsequent_peck`, `peck_clearance`, `retract_amount`, `shift`, `dwell`) and
`drill_cycle_9_custom_parameters` (`parameter_1..10`), plus short names in
`drill_cycle_descriptions` (`custom_drill_9` ...). Custom parameter pages may need to be switched on
in the control definition before they show. Use labels to document units and "0 = default".
Mastercam treats this section as owned by the control definition manager - it may rewrite it, so
compare before each deploy.

## Unused slots

Stop posting with a clear message (cycle number = `drillcyc$ + 1`) instead of writing a
placeholder `M00` - an old job with a removed cycle must not run with nonsense. Reserve slots the
shop will need later the same way ("cycle 15 not implemented yet").

## Heidenhain cycle output

```
CYCL DEF 203 UNIVERSAL-BOHREN ~
  Q200=+2 ;SICHERHEITS-ABST. ~
  Q201=-20 ;TIEFE ~
  ...
  Q203=+0 ;KOORD. OBERFLAECHE ~
  Q204=+50 ;2. SICHERHEITS-ABST.
L X+10 Y+20 FMAX M99
L X+30 Y+20 FMAX M99
```
- One `CYCL DEF` per operation (or per change of a hole dependent value such as Q203), then
  `L X Y FMAX M99` per hole; `CYCL CALL` when the tool already stands on the hole.
- Q200/Q201/Q203/Q204 are relative to the surface (Q203). Build them from `tosz$`, `depth$`,
  `refht$`, `initht$` - and remember that in multiaxis drilling those engine values are relative to
  the hole point.
- Comment texts after `;` are part of the shop's habit - match the old post's spelling.
- Map each dialog field to the Q parameter it feeds and put the Q number into the field label
  (e.g. "Verweilzeit unten (Q211)").
- Tapping: rigid tapping cycles 207/209 take the pitch (Q239) from the tool's thread data - stop
  posting when a tap has no pitch.

## Probing through custom cycles

When the shop has a probe and control cycles but no CAM probing package, custom drill cycles are a
practical carrier:
- One slot per probing cycle family (circle inside / outside, rectangle, slot/web, corner, single
  axis, tool axis, basic rotation, hole circle). The "shift" or a custom parameter selects a
  variant (e.g. two cycles in one slot).
- The drill point is the nominal position (datum value = programmed coordinates).
- Map: depth -> measuring height, clearance -> safe height, a custom parameter -> preset number
  (0 = active), dwell -> "move to safe height between points" (0/1).
- The probe tool: no spindle start, no coolant, no breakage check; stop posting when the probe
  number appears in a cutting or normal drilling operation, and when a probing slot is used with a
  non-probe tool.
- Optional "measure + correct" variants: deviation x factor added to a Q parameter / macro
  variable, with tolerance limits. Agree the sign and factor convention with the shop and write
  the factor into the NC comment.

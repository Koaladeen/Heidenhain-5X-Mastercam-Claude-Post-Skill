# Matching an existing (or encrypted) post from its NC output

Shops often want to replace a vendor post they cannot read or change. The legitimate route: treat
the old post's **NC output** as the specification and rebuild the behaviour on an open base post.
Never decrypt or decode the old post itself.

## Getting good samples

Ask for programs that cover, in this order of value:
1. a typical full part (several tools, several planes / B angles, drilling, contouring),
2. one operation per drill cycle type in the cycle list, in list order (reveals the cycle mapping
   of the old post in one file),
3. special features: tool breakage check, probing, tapping with a real tap, engraving, coolant
   variants, sub-programs,
4. the same program posted with old and new post **on the same day** (dates, times and changed
   operations otherwise pollute the diff).

Also ask for screenshots: misc integer/real dialog of the old post (texts + values), coolant list,
drill cycle list, plane manager values of a few planes. Dialog texts reveal intent ("1 = air", "NP
number 1 = preset 1").

## Diff by category, not by line

Thousands of differing lines are usually a handful of rules. `scripts/nc_diff.py` replaces numbers
by `#`, counts patterns per side, and prints the first hunks of each category. Typical categories
seen in practice:

| Category | Typical cause |
|---|---|
| `X+.2` vs `X+0.2`, `X+12.5` vs `X+12.500` | format flags (leading / trailing zeros) |
| `F2238` vs `F2238.075` | feed decimals |
| `CC`/`C` arc vs `L` for tiny arcs | linearisation rule (sweep angle) |
| `C X.. DR+` vs `C X.. Y.. DR+` | X/Y forced on arcs |
| `PLANE ... TURN` vs `STAY` + rotary axes in the first block | shop preference / setting |
| F after every rapid | feed forcing / format resets |
| extra blocks between operations | null tool changes inside operations |
| `TOOL CALL n Z S..` vs `TOOL CALL S..` | speed change output within a tool |
| different M-codes for coolant | the operations use list entries of the old coolant list |
| missing tool end blocks | 1002 not sent (rotary setup) |
| `TOOL DEF 0` / missing pre-selection | next-tool switch off |
| one rounding difference in a start position | rounding order - usually ignore |

Data differences are not post bugs: if the old dialog list had other entries at the same index,
existing operations now produce other codes. Tell the user which operations to touch.

## Deriving hidden rules from data

Example - **arc linearisation**: the old post wrote some arcs as straight `L` blocks. Collect every
arc that one side wrote as arc and the other as a line, compute radius, chord, arc height and sweep angle from the
NC coordinates (`scripts/arc_rules.py`). Hypotheses that fitted one file and failed on the next:
radius limit, arc height (sagitta). The rule that separated all cases cleanly: **sweep angle
below 0.1 degrees -> line** (largest linearised 0.0979, smallest kept 0.1003). Lesson: test each
hypothesis on a second program before trusting it, and prefer rules that are natural for the
control (angle) over geometric coincidences.

Example - **cycle mapping**: one operation per drill cycle slot, in list order, revealed that the
old post used its own order (which slot gives which `CYCL DEF`), and which dialog field fed which
Q parameter (a field labelled for one value fed another engine variable because the control
definition relabelled it). Field labels can be renamed per cycle in the control definition, so the
engine variable behind a label is not what the label says - verify with distinct values per field.

Example - **tolerance cycle**: `CYCL DEF 32` T matched the sum of two operation tolerance
parameters on almost every tool; the exceptions were old post defaults the shop did not want.
Check exceptions with the user before copying them.

## Deliberate deviations

Shops often want improvements while replacing a post (structure lines, header info, fewer
redundant blocks, combined positioning). Keep them as settings, list them in the revision log, and
exclude them when judging "identical to old" - normalise them away in the diff if they are noisy.

## When the old post is wrong

Old posts have bugs too (e.g. a nonsense dwell word, a default tolerance on one operation type).
Point them out, propose the correct output, let the user decide. Don't copy a bug just to get a
clean diff.

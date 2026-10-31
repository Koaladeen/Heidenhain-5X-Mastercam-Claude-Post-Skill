# NCI, operations and parameters

Observed behaviour in recent Mastercam versions. Parameter numbers were found with a parameter
dump (see mp-language.md, debugging) - they can change between versions; re-verify with a dump.

## gcode$ values around tool changes

| gcode$ | Meaning |
|---|---|
| 1001 | start of file / first tool |
| 1002 | real tool change (may be missing with some rotary setups - track your own flag) |
| 1000 | null tool change: same tool, next operation - **and** breaks inside one operation |
| 1003 | end of file |
| 1005-1008, 1026 | comments (manual entries, operation comment = 1008) |

The pre-read (`pwrtt$`) sees every tool change; a repeated tool may arrive with a negative `t$`.

## Operation identity

- `op_id$` changes per operation, but transform instances and some multi-pass toolpaths reuse it.
- `prv_op_id$` is already updated when the null tool change postblock runs - compare in the
  1002/1000 pre-processing postblock instead, or compare the things that matter (plane, offsets).
- Operation type: `tool_op$` (e.g. multiaxis link / drill link types), and an operation kind
  parameter that separates roughing/finishing families (useful for HSC switches).

## Tool plane

- Matrix rows: `m1$ m2$ m3$` = plane X axis, `m4$ m5$ m6$` = Y axis, `m7$ m8$ m9$` = Z axis (tool
  direction), in WCS/world coordinates.
- `tox$ toy$ toz$`: plane origin in **plane** coordinates (as in the plane manager).
- Multiaxis toolpaths (`mill5$`): coordinates in WCS with tool vector `vtoolx$ vtooly$ vtoolz$`;
  keep the tool plane Top for these unless you transform yourself.

## Arcs

`arcrad$` radius, `sweep$` sweep angle in degrees, `plane$` arc plane. Helical arcs carry Z.

## Parameters found useful (verify in your version)

| What | How it was found |
|---|---|
| tool plane comment (plane corrections) | operation parameter 20011 (20010 = plane name) |
| plane "work offset" field (-1 = auto) | 15166 (tool plane), 15181 (construction plane) |
| operation comment text | 15239 |
| operation kind (rough / finish family) | 15083 |
| chordal / total tolerance | 15136 + 16503 (most toolpaths), helix bore 12391 |
| probing wall distance | 10118 |
| tool stick-out | tool parameter 75011 (also in 20007) |
| stock corners / size | toolpath group parameters 19140-19211, 19125-19127 |

Always confirm with a dump on the user's installation before relying on a number.

## Misc values

`mi1$..mi10$` (integers) and `mr1$..mr10$` (reals) per operation; the dialog texts and defaults
live in the post's text section (`misc_integers` / `misc_reals`). Typical uses: work offset
number, precision level, air, breakage check, tool measurement, park/turn mode, DL/DR. For "per
tool" values decide whether the first operation of the tool or every operation counts, and write
it into the dialog text.

## Canned text

Canned text entries arrive as `cantext$` numbers with a position (before / with / after the move).
Entries 1-4 are reserved for stop / optional stop / block delete on/off in the generic posts; free
entries are good for machine states (brakes release/clamp). X-style coolant arrives as canned text
numbers 50+: list entry k (1 = first) is `50 + 2*(k-1)` for on and one more for off
(50 = entry 1 on, 51 = entry 1 off, 52 = entry 2 on ...) - keep a bit mask of what is on.

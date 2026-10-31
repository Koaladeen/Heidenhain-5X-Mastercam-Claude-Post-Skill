# Serial number engraving with a QR counter (Heidenhain)

Engraves `PREFIX + n digits` at each drill point of an operation. A QR parameter holds the counter
(QR parameters survive power off), it counts up after each number, and an optional start number
raises it. The text comes from the post - no CAM text toolpath, no fonts on the control. Proven on
TNC 530 / 640, also in tilted planes (PLANE SPATIAL) and with text rotation.

## Operation design (a free drill cycle slot)

| Field | Meaning |
|---|---|
| drill point | lower left corner of the first character |
| depth | engraving depth (absolute) |
| retract (R plane) | Z between strokes |
| clearance | Z between numbers / after the text |
| first peck | character height (required, stop posting if 0) |
| subsequent peck | pitch, 0 = 0.8 x height |
| peck clearance | number of digits, 0 = setting (with leading zeros) |
| retract amount | QR number of the counter, 0 = setting |
| shift | plunge feed, 0 = half the engraving feed |
| dwell | text rotation in degrees |
| custom parameter 1 | start number (only raises the counter, never lowers it) |
| operation comment after `#` | prefix text (A-Z 0-9 - / . space) |

Put these meanings into the cycle's dialog labels (post text section) - see
`drill-and-probe-cycles.md`.

## Font

`assets/stroke_font.json`: single-stroke glyphs in a 0.6 wide x 1 high cell, origin lower left.
```
{"chars": "ABCDEFGHIJKLMNOPQRSTUVWXYZ-/. 0123456789",
 "glyph": {"1": [["R",0,0],["ZR"],["ZD"],["F1",0.3,1],["F",0.6,0],["ZR"], ...], ...},
 "digit": {"0": [...], ..., "9": [...]}}
```
Ops: `R u v` rapid to a point at stroke height, `ZR` rapid to stroke height, `ZD` plunge to depth,
`F1 u v` first engraving move (writes the feed), `F u v` next engraving move. `glyph` keys are the
1-based index into `chars` (space has no glyph - it only advances); `digit` holds the digits for
the runtime label subprograms.

Generate the MP code for the font from this file in the build script (one `if ser_ci = n, [...]`
block per glyph, one LBL per digit) instead of typing coordinates.

## Prefix vs digits

- **Prefix** is known when posting: write it inline, glyph by glyph.
- **Digits** depend on the counter at run time: write label subprograms for 0-9 once after the
  main program end (after `M30`, before `END PGM`) and call them per digit position.

## Output outline

```
; SERIENNUMMER SN- + 4 STELLEN AUS QR100 - HOEHE 3
FN 0: Q1720 = -10        ; Z between strokes
FN 0: Q1721 = -42        ; engraving depth
FN 0: Q1722 = +200       ; plunge feed
FN 0: Q1723 = +400       ; engraving feed
Q1701 = QR100
CYCL DEF 7.0 NULLPUNKT   ; incremental shift to the first character
CYCL DEF 7.1 IX+24.5
CYCL DEF 7.2 IY+19
CYCL DEF 7.3 IZ+0
CYCL DEF 26.0 MASSFAKTOR ACHSSPEZ.
CYCL DEF 26.1 X3 Y3 CCX+0 CCY+0          ; X/Y scaled to the character height, Z stays real
L X+0 Y+0 F MAX                           ; prefix glyph in unit coordinates
L Z+Q1720 F MAX
L Z+Q1721 FQ1722
L X+0.3 Y+1 FQ1723
...
CYCL DEF 26.0 MASSFAKTOR ACHSSPEZ.
CYCL DEF 26.1 X1 Y1 CCX+0 CCY+0
(shift by the pitch, next character ...)
Q1710 = INT ( Q1701 / 1000 ) - 10 * INT ( Q1701 / 10000 )   ; digit 1 of 4
(scale on) CALL LBL 900 (scale off)
(shift, next digit ...)
(shift back by the sum of all shifts, clearance height)
QR100 = QR100 + 1
...
M30
LBL 900
FN 9: IF +Q1710 EQU +0 GOTO LBL 910
...
FN 9: IF +Q1710 EQU +9 GOTO LBL 919
LBL 910
L X+0.3 Y+1 F MAX
L Z+Q1720 F MAX
L Z+Q1721 FQ1722
L X+0.2479 Y+0.9924 FQ1723
...
FN 9: IF +0 EQU +0 GOTO LBL 920
...
LBL 920
LBL 0
END PGM ...
```

Details that mattered:
- **Rotation**: `CYCL DEF 10 ROT` only around each glyph (inside the scaling), never around the
  shifts; compute the shifts with cos/sin of the angle in the post. Reset `ROT+0` after the glyph.
- **Shift back**: subtract the sum of the *rounded* shifts that were actually written, otherwise
  rounding leaves the datum a few microns off after many characters.
- **Start number**: `FN 11: IF +QR100 GT +999 GOTO LBL 881` / `QR100 = 1000` / `LBL 881` (unique
  label per operation) - only raises the counter.
- **Comment line**: build it with `no2str()` in a string assignment first (see mp-language.md -
  `no2str` inside the output line gives PST error 94).
- Check that the Q / QR numbers and LBL numbers are free on the machine (other programs, OEM
  cycles).
- Warn (popup at the end) when the prefix contains characters without a glyph.

## Verification

Before the machine: look at the program in the TNC's test run graphics (or a CAM backplot of the
`.h`) for a few counter values. Check prefix and digits line up, leading zeros, rotation, and that
the counter increments. Then dry-run above the part.

# mastercam-heidenhain-posts - a Claude skill for Mastercam posts on Heidenhain TNC

A [Claude Code](https://claude.com/claude-code) skill that helps Claude build, modify, debug and
verify Mastercam MP post processors (`.pst`) for **Heidenhain TNC** controls (Klartext,
TNC 530 / 620 / 640): 3-axis, 3+2 with `PLANE SPATIAL`, 5-axis TCPM with `LN` radius compensation,
`CYCL DEF` drill cycles, `TCH PROBE` probing through custom drill cycles, serial number engraving
with a QR counter, tool call / brake / coolant logic - and replacing a vendor post you cannot read
by matching its `.h` output line by line.

It is field experience from real shop projects, written down as rules, traps and checklists, plus
a few small Python tools. It is **not** a copy of Mastercam's or Heidenhain's documentation or
posts.

Documentation page: `docs/index.html`.

## What's inside

```
skills/mastercam-heidenhain-posts/
  SKILL.md                         workflow, ground rules, the ten most expensive traps
  references/
    mp-language.md                 MP syntax/format traps, engine behaviour, debugging
    workflow.md                    build scripts, settings block, backups, safe deploy, testing loop
    matching-old-posts.md          cloning an old/encrypted post from its NC output
    heidenhain-tnc.md              program frame, TOOL CALL, CYCL 32, PLANE SPATIAL, TCPM, brakes, extras
    drill-and-probe-cycles.md      CYCL DEF output, cycle slots, field mapping, labels, TCH PROBE
    serial-engraving.md            QR counter + built-in single-stroke font, LBL subprograms
    nci-and-parameters.md          NCI codes, operations, tool plane matrix, useful parameter numbers
  scripts/
    patch_tool.py                  asserted text replacements for build scripts + static post check
    nc_diff.py                     old vs new .h diff without block numbers, grouped by pattern
    arc_rules.py                   find the arc linearisation rule of a post from CC/C/L data
    safe_deploy.py                 hash check -> backup -> copy -> verify
  assets/
    stroke_font.json               single-stroke engraving font (A-Z, 0-9, - / .)
  evals/                           test cases (synthetic data) for the skill
```

## Install

Copy the skill folder into your Claude Code skills directory:

```bash
# for you, in every project
cp -r skills/mastercam-heidenhain-posts ~/.claude/skills/
# or only for one project (shared with everyone who works in that folder)
cp -r skills/mastercam-heidenhain-posts <your-project>/.claude/skills/
```

Claude picks the skill up automatically when you work on posts for Heidenhain machines, MP code,
NCI questions or NC output comparisons. The scripts need Python 3 only.

## Using it well

- Give Claude `.h` samples from your current post and screenshots of the dialogs (misc values,
  coolant list, drill cycle list, plane manager). The skill is built around "the old NC output is
  the specification".
- Keep your live posts where Claude only copies after you say so. The skill insists on backups,
  hash checks and explicit deploys - keep it that way.
- You still need your own licensed Mastercam installation and its base posts / MP documentation,
  and the Heidenhain cycle documentation for your control. This repository contains none of them.

## Safety disclaimer

**NC code moves heavy machines. A post processor error can crash a spindle, scrap a part or hurt
someone.** Everything here is provided as is, without warranty of any kind (see LICENSE). Always
verify posted programs in the control's test run graphics, then with a dry run on the machine with
Z backed off, before cutting. Machine-specific M-codes, Q/QR parameters, travel limits and options
in the examples are examples only - take the real values from your machine's documentation.

## Legal

- MIT licensed (see `LICENSE`).
- Mastercam is a trademark of CNC Software, LLC. Heidenhain and TNC are trademarks of
  DR. JOHANNES HEIDENHAIN GmbH. This project is independent and not affiliated with, endorsed or
  sponsored by either of them.
- No Mastercam post code, MP documentation text, Heidenhain manual text, or content from
  encrypted/vendor posts is included. Predefined variable and postblock names are mentioned only
  as interface names.
- The examples are anonymised; machine and part numbers in examples are made up or generic.

## Contributing

Corrections and additions are welcome - other TNC versions, other kinematics, probing variants,
version differences in NCI parameters. Please keep contributions free of your company's or
customers' data and of vendor-owned code or manual text.

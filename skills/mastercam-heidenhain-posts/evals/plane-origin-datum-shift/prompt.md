---
tags: [skill-creator]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

I'm writing my own Mastercam post for a TNC 640 with an A/C table. For 3+2 operations the old post writes an absolute CYCL DEF 7 datum shift to the plane origin and then PLANE SPATIAL ... STAY, and the A and C axes come in the first positioning block. In my post the CYCL DEF 7 values are wrong as soon as the tool plane is tilted and has its origin somewhere else than 0,0,0. Also it does a complete new PLANE setup on every operation even if the plane is the same. Explain what is wrong and write the MP code for the datum shift and the 'same plane?' check. Put the code in plane_setup.txt.

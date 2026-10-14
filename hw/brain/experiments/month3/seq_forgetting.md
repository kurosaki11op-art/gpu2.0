# Sequence memory (SPARK-L lookup core) across text domains - SIMULATED, 15 Oct 2026

Reference model `hw/system/lookup_ref.py` LookupCoreV2. Learn 16 KB of code, then read 80 KB of prose; measure
next-byte accuracy on 4 KB of held-out code (learning stays on while reading it, from a copy of the state).

| Tables | after code | after code then prose | never saw code |
|---|---|---|---|
| TB=11 (block-RAM size on the board) | 0.813 | 0.757 | 0.731 |
| TB=13 (4x larger) | 0.813 | 0.780 | 0.730 |

Reading: the sequence memory keeps ~32% (TB=11) / ~60% (TB=13) of what code taught it after a domain change; the loss
comes from table capacity (hashed slots get reused). For month 6 (sequence memory joins the cortex) this means more
capacity (PSRAM) or a context mechanism like the cortex's frozen dream memory.

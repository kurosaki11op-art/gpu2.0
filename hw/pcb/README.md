# SPARK power-measurement board (KiCad 7) — v0.1

An inline USB-C power meter for the SPARK FPGA prototype:
laptop USB-C (J1) → 0.1 Ω shunt (RS1) → USB-C (J2) → Sipeed Tang Nano 20K. USB 2.0 data passes straight through.
INA219 (U1) measures shunt current and bus voltage, LM75 (U2) board temperature, J5 takes a DS18B20 probe for the
FPGA package, J3 takes the FPGA's benchmark marker wire, and J4 connects any ESP32 board (3V3, GND, SDA, SCL, MARKER, DQ).
Powering the Tang Nano through its own USB-C port avoids any assumption about its header pinout.

| File | What |
|---|---|
| `design.py` | Single source of truth: parts, footprints, every pin → net |
| `make_sch.py` → `spark_meter.kicad_sch` | Schematic (official KiCad library symbols) |
| `make_pcb.py` → `spark_meter.kicad_pcb` | 2-layer 72 × 52 mm board, placement, Freerouting autoroute, GND pours |
| `verify_sch.py`, `run_drc.py` | Verification (below) |
| `fab/` | Gerbers, drill file, pick-and-place |
| `img/` | Schematic (PDF/SVG/PNG) and board renders |

## Verification (reproduce: `python3 make_sch.py && kicad-cli sch export netlist --format kicadsexpr -o spark_meter.net spark_meter.kicad_sch && python3 verify_sch.py && python3 make_pcb.py place && xvfb-run -a java -jar freerouting-1.9.0.jar -de spark_meter.dsn -do spark_meter.ses -mp 30 && python3 make_pcb.py finish && python3 run_drc.py`)
| Check | Tool | Result |
|---|---|---|
| Schematic connectivity: every pin on the intended net | netlist exported by KiCad from the schematic vs `design.py` | 92 pins, 15 nets + 5 intentional no-connects, **0 errors** (107 checks) |
| Electrical rules: single-pin nets, undriven power inputs, multiple drivers, undriven inputs | `verify_sch.py` (KiCad 7 CLI has no ERC) | **0 errors** |
| Design-rule check | KiCad DRC engine (`pcbnew.WriteDRCReport`) | **0 errors, 0 warnings, 0 unconnected** |
| PCB ↔ schematic parity | every PCB pad net vs KiCad's schematic netlist | 98 pads, **0 mismatches** |

Rules: 0.2 mm signal / 0.5 mm power tracks, 0.15 mm clearance, 0.6/0.3 mm vias, 0.3 mm copper-to-edge.
Hole clearance is set to 0.18 mm because the GCT USB4105 manufacturer land pattern places its locating pegs
0.194 mm from the GND pads; confirm with the PCB fab.

## Known limits before ordering (v0.2)
- The INA219 sense inputs connect through the VBUS nets, not dedicated Kelvin traces at the shunt pads
  (adds an error of roughly trace resistance / 100 mΩ, ~1–2 %).
- USB D+/D− are routed as plain tracks, not an impedance-controlled 90 Ω pair; fine for full speed, check for high speed.
- Not built or bench-tested yet. Component values follow the INA219 / LM75 datasheets' typical circuits.

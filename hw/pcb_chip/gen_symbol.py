"""SPARK chip symbol (QFN-32 + exposed pad) for KiCad 7: writes spark.kicad_sym.
Pinout is the package plan for the SKY130 SPARK chip (spark_chip.v): 8 signal pins, split 1.8 V core (VCCD)
and 3.3 V I/O (VDDIO) supplies, ground on 8 pins + exposed pad."""
PINS = {  # number: (name, electrical type)
    1: ('VDDIO', 'power_in'), 2: ('UART_RX', 'input'), 3: ('UART_TX', 'output'), 4: ('VSS', 'power_in'),
    5: ('VCCD', 'power_in'), 6: ('RST_N', 'input'), 7: ('VSS', 'power_in'), 8: ('CLK', 'input'),
    9: ('VDDIO', 'power_in'), 10: ('READY', 'output'), 11: ('BUSY', 'output'), 12: ('TOK', 'output'),
    13: ('TRIG', 'output'), 14: ('VSS', 'power_in'), 15: ('VCCD', 'power_in'), 16: ('VSS', 'power_in'),
    17: ('VDDIO', 'power_in'), 18: ('RSVD', 'no_connect'), 19: ('RSVD', 'no_connect'), 20: ('VSS', 'power_in'),
    21: ('VCCD', 'power_in'), 22: ('RSVD', 'no_connect'), 23: ('RSVD', 'no_connect'), 24: ('VSS', 'power_in'),
    25: ('VDDIO', 'power_in'), 26: ('RSVD', 'no_connect'), 27: ('RSVD', 'no_connect'), 28: ('VSS', 'power_in'),
    29: ('VCCD', 'power_in'), 30: ('RSVD', 'no_connect'), 31: ('RSVD', 'no_connect'), 32: ('VSS', 'power_in'),
    33: ('VSS', 'power_in'),
}
LEFT = [1, 9, 17, 25, 5, 15, 21, 29, 2, 6, 8, 18, 19, 22, 23, 26, 27]    # supplies + inputs + reserved
RIGHT = [3, 10, 11, 12, 13, 30, 31, 4, 7, 14, 16, 20, 24, 28, 32, 33]   # outputs + reserved + grounds
P = 2.54
H = max(len(LEFT), len(RIGHT)) * P
def pin(num, x, y, rot):
    name, typ = PINS[num]
    hide = ' hide' if typ == 'no_connect' and False else ''
    return (f'      (pin {typ} line (at {x} {y} {rot}) (length 2.54){hide}\n'
            f'        (name "{name}" (effects (font (size 1.27 1.27))))\n'
            f'        (number "{num}" (effects (font (size 1.27 1.27)))))')
lines = []
for i, n in enumerate(LEFT):
    lines.append(pin(n, -17.78, round(H / 2 - P - i * P, 2), 0))
for i, n in enumerate(RIGHT):
    lines.append(pin(n, 17.78, round(H / 2 - P - i * P, 2), 180))
sym = f'''(kicad_symbol_lib (version 20220914) (generator spark_gen)
  (symbol "SPARK_QFN32" (in_bom yes) (on_board yes)
    (property "Reference" "U" (at 0 {round(H / 2 + 2.54, 2)} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "SPARK_QFN32" (at 0 {round(-H / 2 - 2.54, 2)} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (symbol "SPARK_QFN32_0_1"
      (rectangle (start -15.24 {round(H / 2, 2)}) (end 15.24 {round(-H / 2, 2)}) (stroke (width 0.254) (type default)) (fill (type background)))
    )
    (symbol "SPARK_QFN32_1_1"
{chr(10).join(lines)}
    )
  )
)
'''
open('spark.kicad_sym', 'w').write(sym)
print('symbol: 33 pins')

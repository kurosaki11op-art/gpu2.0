"""SPARK chip evaluation board: single source of truth for the schematic and the PCB.

USB-C (J1) -> 3.3 V LDO (U3) -> 1.8 V LDO (U4) -> 0.1 ohm shunt (RS1) -> SPARK chip core supply (VCCD).
INA219 (U5) measures the chip's own core current and voltage. CH340C (U2) bridges USB to the chip UART.
27 MHz oscillator (Y1) clocks the chip; reset button + RC on RST_N; LEDs on READY, BUSY, TOK.
J2 connects an ESP32 power logger (I2C + benchmark marker), J3 is a debug UART header.
"""
PROJECT = 'spark_chip_board'
TITLE = 'SPARK chip evaluation board'
COMMENTS = ['SKY130 SPARK chip (QFN-32) + power measurement on the 1.8 V core rail',
            'USB-C -> CH340C UART bridge, AP2112K 3.3 V / 1.8 V LDOs, INA219 core-rail monitor']

C100N = ('Device:C', '100nF', 'Capacitor_SMD:C_0603_1608Metric')
C1U = ('Device:C', '1uF', 'Capacitor_SMD:C_0603_1608Metric')
C10U = ('Device:C', '10uF', 'Capacitor_SMD:C_0805_2012Metric')
R0603 = 'Resistor_SMD:R_0603_1608Metric'
CHIP = {1: '+3V3', 9: '+3V3', 17: '+3V3', 25: '+3V3', 5: 'VCCD', 15: 'VCCD', 21: 'VCCD', 29: 'VCCD',
        4: 'GND', 7: 'GND', 14: 'GND', 16: 'GND', 20: 'GND', 24: 'GND', 28: 'GND', 32: 'GND', 33: 'GND',
        2: 'UART_RX', 3: 'UART_TX', 6: 'RST_N', 8: 'CLK', 10: 'READY', 11: 'BUSY', 12: 'TOK', 13: 'TRIG',
        18: None, 19: None, 22: None, 23: None, 26: None, 27: None, 30: None, 31: None}

PARTS = {
    'U1': ('spark:SPARK_QFN32', 'SPARK (SKY130)', 'Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm',
           {str(k): v for k, v in CHIP.items()}),
    'J1': ('Connector:USB_C_Receptacle_USB2.0_16P', 'USB-C (power + UART)', 'Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal',
           {'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND', 'A4': 'VBUS', 'A9': 'VBUS', 'B4': 'VBUS', 'B9': 'VBUS',
            'A5': 'CC1', 'B5': 'CC2', 'A6': 'USB_DP', 'B6': 'USB_DP', 'A7': 'USB_DN', 'B7': 'USB_DN', 'A8': None, 'B8': None, 'S1': 'GND'}),
    'R1': ('Device:R', '5.1k', R0603, {'1': 'CC1', '2': 'GND'}),
    'R2': ('Device:R', '5.1k', R0603, {'1': 'CC2', '2': 'GND'}),
    'U2': ('Interface_USB:CH340C', 'CH340C', 'Package_SO:SOIC-16_3.9x9.9mm_P1.27mm',
           {'1': 'GND', '2': 'UART_RX', '3': 'UART_TX', '4': '+3V3', '5': 'USB_DP', '6': 'USB_DN', '7': None, '8': None,
            '9': None, '10': None, '11': None, '12': None, '13': None, '14': None, '15': 'GND', '16': '+3V3'}),
    'C1': (*C100N, {'1': '+3V3', '2': 'GND'}),
    'U3': ('Regulator_Linear:AP2112K-3.3', 'AP2112K-3.3', 'Package_TO_SOT_SMD:SOT-23-5',
           {'1': 'VBUS', '2': 'GND', '3': 'VBUS', '4': None, '5': '+3V3'}),
    'C2': (*C1U, {'1': 'VBUS', '2': 'GND'}),
    'C3': (*C10U, {'1': '+3V3', '2': 'GND'}),
    'U4': ('Regulator_Linear:AP2112K-1.8', 'AP2112K-1.8', 'Package_TO_SOT_SMD:SOT-23-5',
           {'1': '+3V3', '2': 'GND', '3': '+3V3', '4': None, '5': 'VCCD_IN'}),
    'C4': (*C1U, {'1': '+3V3', '2': 'GND'}),
    'C5': (*C1U, {'1': 'VCCD_IN', '2': 'GND'}),
    'RS1': ('Device:R', '0.1R 1%', 'Resistor_SMD:R_1206_3216Metric', {'1': 'VCCD_IN', '2': 'VCCD'}),
    'U5': ('Sensor_Energy:INA219AxD', 'INA219AID', 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
           {'1': 'GND', '2': 'GND', '3': 'SDA', '4': 'SCL', '5': '+3V3', '6': 'GND', '7': 'VCCD', '8': 'VCCD_IN'}),
    'C6': (*C100N, {'1': '+3V3', '2': 'GND'}),
    'R3': ('Device:R', '4.7k', R0603, {'1': '+3V3', '2': 'SDA'}),
    'R4': ('Device:R', '4.7k', R0603, {'1': '+3V3', '2': 'SCL'}),
    'C7': (*C100N, {'1': 'VCCD', '2': 'GND'}), 'C8': (*C100N, {'1': 'VCCD', '2': 'GND'}),
    'C9': (*C100N, {'1': 'VCCD', '2': 'GND'}), 'C10': (*C100N, {'1': 'VCCD', '2': 'GND'}),
    'C11': (*C10U, {'1': 'VCCD', '2': 'GND'}),
    'C12': (*C100N, {'1': '+3V3', '2': 'GND'}), 'C13': (*C100N, {'1': '+3V3', '2': 'GND'}),
    'C14': (*C100N, {'1': '+3V3', '2': 'GND'}), 'C15': (*C100N, {'1': '+3V3', '2': 'GND'}),
    'Y1': ('Oscillator:ASE-xxxMHz', '27 MHz', 'Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm',
           {'1': '+3V3', '2': 'GND', '3': 'OSC_OUT', '4': '+3V3'}),
    'C16': (*C100N, {'1': '+3V3', '2': 'GND'}),
    'R5': ('Device:R', '22R', R0603, {'1': 'OSC_OUT', '2': 'CLK'}),
    'R6': ('Device:R', '10k', R0603, {'1': '+3V3', '2': 'RST_N'}),
    'C17': (*C1U, {'1': 'RST_N', '2': 'GND'}),
    'SW1': ('Switch:SW_Push', 'RESET', 'Button_Switch_SMD:SW_SPST_PTS645', {'1': 'RST_N', '2': 'GND'}),
    'R7': ('Device:R', '1k', R0603, {'1': 'READY', '2': 'LED_RDY'}),
    'D1': ('Device:LED', 'READY', 'LED_SMD:LED_0603_1608Metric', {'1': 'GND', '2': 'LED_RDY'}),
    'R8': ('Device:R', '1k', R0603, {'1': 'BUSY', '2': 'LED_BSY'}),
    'D2': ('Device:LED', 'BUSY', 'LED_SMD:LED_0603_1608Metric', {'1': 'GND', '2': 'LED_BSY'}),
    'R9': ('Device:R', '1k', R0603, {'1': 'TOK', '2': 'LED_TOK'}),
    'D3': ('Device:LED', 'TOKEN', 'LED_SMD:LED_0603_1608Metric', {'1': 'GND', '2': 'LED_TOK'}),
    'J2': ('Connector_Generic:Conn_01x06', 'ESP32 logger (3V3 GND SDA SCL TRIG TOK)', 'Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical',
           {'1': '+3V3', '2': 'GND', '3': 'SDA', '4': 'SCL', '5': 'TRIG', '6': 'TOK'}),
    'J3': ('Connector_Generic:Conn_01x03', 'Debug UART (GND RX TX)', 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',
           {'1': 'GND', '2': 'UART_RX', '3': 'UART_TX'}),
    'TP1': ('Connector:TestPoint', 'VCCD 1.8V', 'TestPoint:TestPoint_Pad_D1.5mm', {'1': 'VCCD'}),
    'TP2': ('Connector:TestPoint', '+3V3', 'TestPoint:TestPoint_Pad_D1.5mm', {'1': '+3V3'}),
    'TP3': ('Connector:TestPoint', 'GND', 'TestPoint:TestPoint_Pad_D1.5mm', {'1': 'GND'}),
    'TP4': ('Connector:TestPoint', 'CLK', 'TestPoint:TestPoint_Pad_D1.5mm', {'1': 'CLK'}),
    'H1': ('Mechanical:MountingHole', 'M3', 'MountingHole:MountingHole_3.2mm_M3', {}),
    'H2': ('Mechanical:MountingHole', 'M3', 'MountingHole:MountingHole_3.2mm_M3', {}),
    'H3': ('Mechanical:MountingHole', 'M3', 'MountingHole:MountingHole_3.2mm_M3', {}),
    'H4': ('Mechanical:MountingHole', 'M3', 'MountingHole:MountingHole_3.2mm_M3', {}),
}
PWR_FLAGS = ['GND', '+3V3', 'VBUS', 'VCCD', 'VCCD_IN']
POWER_NETS = ['VBUS']                      # 0.4 mm; chip rails use 0.25 mm to reach the 0.5 mm-pitch QFN pins

# schematic placement (mm, 2.54 grid, A3)
_grid = [r for r in PARTS if r not in ('U1', 'J1', 'U2', 'U5') and not r.startswith('H')]
LAYOUT = {'U1': (190.5, 127.0), 'J1': (40.64, 71.12), 'U2': (101.6, 71.12), 'U5': (279.4, 71.12)}
for i, ref in enumerate(_grid):
    LAYOUT[ref] = (40.64 + (i % 12) * 30.48, 175.26 + (i // 12) * 30.48 if i >= 0 else 0)
LAYOUT.update({'H1': (330.2, 256.54), 'H2': (345.44, 256.54), 'H3': (360.68, 256.54), 'H4': (375.92, 256.54)})
FLAG_POS = [(355.6, 35.56), (368.3, 35.56), (381.0, 35.56), (393.7, 35.56), (406.4, 35.56)]

# PCB: 60 x 46 mm, (x, y, rotation)
W, H = 60.0, 46.0
PLACE = {
    'J1': (3.675, 23.0, 270), 'R1': (10.5, 29.0, 90), 'R2': (13.5, 29.0, 90),
    'U2': (16.0, 12.0, 0), 'C1': (21.5, 6.0, 0),
    'U3': (12.0, 37.5, 0), 'C2': (8.5, 41.0, 0), 'C3': (16.0, 41.0, 0),
    'U4': (23.0, 37.5, 0), 'C4': (20.0, 41.0, 0), 'C5': (26.5, 41.0, 0),
    'RS1': (31.0, 37.5, 0), 'U5': (40.0, 38.0, 0), 'C6': (40.0, 33.0, 0), 'R3': (46.0, 41.0, 90), 'R4': (49.5, 41.0, 90),
    'U1': (32.0, 21.0, 0),
    'C7': (26.0, 17.0, 90), 'C8': (38.0, 25.0, 90), 'C9': (28.5, 27.5, 0), 'C10': (35.5, 14.0, 0), 'C11': (31.0, 31.5, 0),
    'C12': (25.5, 25.5, 90), 'C13': (38.0, 17.0, 90), 'C14': (31.5, 14.0, 0), 'C15': (32.0, 28.0, 0),
    'Y1': (44.0, 21.0, 0), 'C16': (44.0, 25.5, 0), 'R5': (39.5, 21.0, 0),
    'R6': (21.5, 11.5, 90), 'C17': (25.0, 11.5, 90), 'SW1': (30.0, 6.0, 0),
    'R7': (50.0, 8.0, 0), 'D1': (54.0, 8.0, 0), 'R8': (50.0, 11.0, 0), 'D2': (54.0, 11.0, 0), 'R9': (50.0, 14.0, 0), 'D3': (54.0, 14.0, 0),
    'J2': (56.0, 20.0, 0), 'J3': (51.5, 30.0, 0),
    'TP1': (35.0, 33.0, 0), 'TP2': (21.0, 31.0, 0), 'TP3': (46.0, 33.0, 0), 'TP4': (44.0, 16.5, 0),
    'H1': (3.5, 3.5, 0), 'H2': (W - 3.5, 3.5, 0), 'H3': (3.5, H - 3.5, 0), 'H4': (W - 3.5, H - 3.5, 0),
}
TEXTS = [('SPARK chip board v0.1', 30.0, 44.6, 1.2), ('USB-C', 9.5, 16.5, 0.9), ('SKY130 SPARK', 41.0, 4.0, 0.8)]

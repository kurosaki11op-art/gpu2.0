"""SPARK power-measurement board: the single source of truth for schematic and PCB.

An inline USB-C power meter for the SPARK FPGA prototype:
  laptop USB-C (J1) -> 0.1 ohm shunt (RS1) -> USB-C (J2) -> Tang Nano 20K
USB 2.0 data passes straight through. An INA219 (U1) measures the shunt current and bus voltage,
an LM75 (U2) measures board temperature, a header takes a DS18B20 probe for the FPGA package,
and a 6-pin header (J4) connects any ESP32 board (I2C + marker + 1-wire) for logging.
Using the Tang Nano's own USB port avoids any assumption about its header pinout.
"""

# ref: (lib_id, value, footprint, {pin_number: net})   pin numbers = KiCad symbol pin numbers
PARTS = {
    'J1': ('Connector:USB_C_Receptacle_USB2.0_16P', 'USB-C IN (laptop)', 'Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal',
           {'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND', 'A4': 'VBUS_IN', 'A9': 'VBUS_IN', 'B4': 'VBUS_IN', 'B9': 'VBUS_IN',
            'A5': 'CC1_IN', 'B5': 'CC2_IN', 'A6': 'USB_DP', 'B6': 'USB_DP', 'A7': 'USB_DN', 'B7': 'USB_DN', 'A8': None, 'B8': None, 'S1': 'GND'}),
    'J2': ('Connector:USB_C_Receptacle_USB2.0_16P', 'USB-C OUT (Tang Nano 20K)', 'Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal',
           {'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND', 'A4': 'VBUS_OUT', 'A9': 'VBUS_OUT', 'B4': 'VBUS_OUT', 'B9': 'VBUS_OUT',
            'A5': 'CC1_OUT', 'B5': 'CC2_OUT', 'A6': 'USB_DP', 'B6': 'USB_DP', 'A7': 'USB_DN', 'B7': 'USB_DN', 'A8': None, 'B8': None, 'S1': 'GND'}),
    'RS1': ('Device:R', '0.1R 1% 1W', 'Resistor_SMD:R_2512_6332Metric', {'1': 'VBUS_IN', '2': 'VBUS_OUT'}),
    'U1': ('Sensor_Energy:INA219AxD', 'INA219AID', 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
           {'1': 'GND', '2': 'GND', '3': 'SDA', '4': 'SCL', '5': '+3V3', '6': 'GND', '7': 'VBUS_OUT', '8': 'VBUS_IN'}),
    'U2': ('Sensor_Temperature:LM75C', 'LM75BD', 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
           {'1': 'SDA', '2': 'SCL', '3': None, '4': 'GND', '5': 'GND', '6': 'GND', '7': 'GND', '8': '+3V3'}),
    'R1': ('Device:R', '5.1k', 'Resistor_SMD:R_0603_1608Metric', {'1': 'CC1_IN', '2': 'GND'}),
    'R2': ('Device:R', '5.1k', 'Resistor_SMD:R_0603_1608Metric', {'1': 'CC2_IN', '2': 'GND'}),
    'R3': ('Device:R', '56k', 'Resistor_SMD:R_0603_1608Metric', {'1': 'VBUS_OUT', '2': 'CC1_OUT'}),
    'R4': ('Device:R', '56k', 'Resistor_SMD:R_0603_1608Metric', {'1': 'VBUS_OUT', '2': 'CC2_OUT'}),
    'R5': ('Device:R', '4.7k', 'Resistor_SMD:R_0603_1608Metric', {'1': '+3V3', '2': 'SDA'}),
    'R6': ('Device:R', '4.7k', 'Resistor_SMD:R_0603_1608Metric', {'1': '+3V3', '2': 'SCL'}),
    'R7': ('Device:R', '4.7k', 'Resistor_SMD:R_0603_1608Metric', {'1': '+3V3', '2': 'TEMP_DQ'}),
    'R8': ('Device:R', '1k', 'Resistor_SMD:R_0603_1608Metric', {'1': 'VBUS_IN', '2': 'LED_A'}),
    'D1': ('Device:LED', 'Power LED', 'LED_SMD:LED_0603_1608Metric', {'1': 'GND', '2': 'LED_A'}),
    'C1': ('Device:C', '100nF', 'Capacitor_SMD:C_0603_1608Metric', {'1': '+3V3', '2': 'GND'}),
    'C2': ('Device:C', '100nF', 'Capacitor_SMD:C_0603_1608Metric', {'1': '+3V3', '2': 'GND'}),
    'C3': ('Device:C', '10uF', 'Capacitor_SMD:C_0805_2012Metric', {'1': 'VBUS_OUT', '2': 'GND'}),
    'C4': ('Device:C', '10uF', 'Capacitor_SMD:C_0805_2012Metric', {'1': 'VBUS_IN', '2': 'GND'}),
    'J3': ('Connector_Generic:Conn_01x02', 'MARKER from FPGA', 'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',
           {'1': 'MARKER', '2': 'GND'}),
    'J4': ('Connector_Generic:Conn_01x06', 'To ESP32 (3V3 GND SDA SCL MARK DQ)', 'Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical',
           {'1': '+3V3', '2': 'GND', '3': 'SDA', '4': 'SCL', '5': 'MARKER', '6': 'TEMP_DQ'}),
    'J5': ('Connector_Generic:Conn_01x03', 'DS18B20 probe on FPGA', 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',
           {'1': '+3V3', '2': 'TEMP_DQ', '3': 'GND'}),
    'TP1': ('Connector:TestPoint', 'VBUS_IN', 'TestPoint:TestPoint_Pad_D1.5mm', {'1': 'VBUS_IN'}),
    'TP2': ('Connector:TestPoint', 'VBUS_OUT', 'TestPoint:TestPoint_Pad_D1.5mm', {'1': 'VBUS_OUT'}),
    'TP3': ('Connector:TestPoint', 'GND', 'TestPoint:TestPoint_Pad_D1.5mm', {'1': 'GND'}),
    'H1': ('Mechanical:MountingHole', 'M3', 'MountingHole:MountingHole_3.2mm_M3', {}),
    'H2': ('Mechanical:MountingHole', 'M3', 'MountingHole:MountingHole_3.2mm_M3', {}),
    'H3': ('Mechanical:MountingHole', 'M3', 'MountingHole:MountingHole_3.2mm_M3', {}),
    'H4': ('Mechanical:MountingHole', 'M3', 'MountingHole:MountingHole_3.2mm_M3', {}),
}
PWR_FLAGS = ['GND', '+3V3', 'VBUS_IN', 'VBUS_OUT']
POWER_NETS = {'VBUS_IN', 'VBUS_OUT', 'GND'}

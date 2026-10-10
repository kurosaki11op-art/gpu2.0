# SPARK floorplan on the GW2AR-18 FPGA

`python3 floorplan.py ../pnr2/pnr2.json spark_floorplan.png` draws every cell that nextpnr placed for the SPARK
board design (22,117 cells on the 56 × 51-tile die) at its real tile position, coloured by SPARK block
(name-based grouping). Squares are block RAMs. Source: the place-and-route run that met timing (54 MHz vs 27 MHz).

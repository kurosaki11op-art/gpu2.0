cd /home/user/gpu2.0/hw/asic/cortex
OUT=floor2c ITER=64 timeout 30000 /opt/eda_or/bin/openroad -no_init -exit route3.tcl > floor2c/route_full.log 2>&1
echo "route3 finished" >> floor2c/route_full.log

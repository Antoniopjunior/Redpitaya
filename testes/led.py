#!/usr/bin/python3

import sys
import redpitaya_scpi as scpi
import time

# exemplo de led acendendo aos poucos 
IP = '10.42.0.236'
rp_s = scpi.scpi(IP)


value = 0
if len(sys.argv) > (2):
    value = sys.argv[2]

for i in range(6):
    value+=0.5
    rp_s.tx_txt('ANALOG:PIN AOUT' + str(3) + ',' + str(value))
    print ("Voltage setting for AO["+str(3)+"] = "+str(value)+"V")
    time.sleep(1)
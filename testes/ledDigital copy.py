#!/usr/bin/env python3

# import sys
import redpitaya_scpi as scpi
import time

IP = '10.42.0.236'
rp = scpi.scpi(IP)


rp.tx_txt('DIG:PIN:DIR OUT,DIO0_N') #Definindo o pino digital DIO0 como saída
rp.tx_txt('DIG:PIN DIO0_N, 0') #Definindo que ele comece sempre como "nível lógico baixo"




rp.close()
#!/usr/bin/env python3

# import sys
import redpitaya_scpi as scpi
import time

IP = '10.42.0.236' #chamada do IP da RedPitaya
rp = scpi.scpi(IP)


rp.tx_txt('DIG:PIN:DIR OUT,DIO3_N') #Definindo o DIO 0 como pino de saída
rp.tx_txt('DIG:PIN DIO3_N, 0') # "Escrevendo" o nível "lógico" baixo para o pino
    

while 1: #laço de repetição que faz o led piscar
    rp.tx_txt('DIG:PIN DIO3_N,1')
    time.sleep(1)
    rp.tx_txt('DIG:PIN DIO3_N,0')
    time.sleep(1)




rp.close()
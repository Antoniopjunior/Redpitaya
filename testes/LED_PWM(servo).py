#!/usr/bin/env python3
import redpitaya_scpi as scpi
import time
import math

# Configuração
IP = "10.42.0.236"
rp = scpi.scpi(IP)

rp.tx_txt('DIG:PIN:DIR OUT,DIO0_N') 
rp.tx_txt('DIG:PIN DIO0_N, 0') 

def map_value(x, in_min, in_max, out_min, out_max):
    """Função para mapear valores de uma faixa para outra"""
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def moveServo(angle):
    pulseWidth = map_value(angle, 0, 180, 500, 2500)
    
    pulse_duration = pulseWidth / 1000000.0  
    rp.tx_txt('DIG:PIN DIO0_N, 1')
    time.sleep(pulse_duration)
    rp.tx_txt('DIG:PIN DIO0_N, 0')
    
    
    time.sleep(0.02 - pulse_duration)

# Testando o servo
for i in range(0, 181, 1):  # Movendo de 0 a 180 graus
    moveServo(i)
    time.sleep(0.015)  # Pequena pausa entre movimentos

# Retornando à posição inicial
for i in range(180, -1, -1):  # Movendo de 180 a 0 graus
    moveServo(i)
    time.sleep(0.015)

rp.tx_txt('DIG:PIN DIO0_N, 0')
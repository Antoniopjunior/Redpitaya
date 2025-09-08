#!/usr/bin/env python3
import redpitaya_scpi as scpi
import time
import math

# Configuração
IP = "10.42.0.236"
rp = scpi.scpi(IP)
LED_PIN = 'DIO0_N'

def setup_led():
    rp.tx_txt(f'DIG:PIN:DIR OUT,{LED_PIN}')
    rp.tx_txt(f'DIG:PIN {LED_PIN},0')

def set_led_brightness(duty_cycle, cycle_duration=0.05):
    """Controla o brilho com PWM por software"""
    on_time = cycle_duration * (duty_cycle / 100.0)
    off_time = cycle_duration - on_time
    
    rp.tx_txt(f'DIG:PIN {LED_PIN},1')
    time.sleep(on_time)
    rp.tx_txt(f'DIG:PIN {LED_PIN},0')
    time.sleep(off_time)

def smooth_breathing():
    """Efeito de respiração mais suave"""
    try:
        setup_led()
        
        while True:
            # Respiração mais lenta e suave
            for i in range(200):
                # Usando função seno para transição suave
                brightness = 50 + 60 * math.sin(i * 0.05)
                set_led_brightness(max(0, min(100, brightness)), 0.01)
                
    except KeyboardInterrupt:
        rp.tx_txt(f'DIG:PIN {LED_PIN},0')
        rp.close()

if __name__ == "__main__":
    smooth_breathing()
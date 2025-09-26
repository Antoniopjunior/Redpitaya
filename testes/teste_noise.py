import redpitaya_scpi as scpi
import numpy as np
import time
import math

# Configuração inicial
rp = scpi.scpi('10.42.0.25')  # IP da sua Red Pitaya

# Configurações do servo
CENTER_ANGLE = 90
MAX_ANGLE_RANGE = 30

def read_single_value(canal):
    rp.tx_txt('ACQ:DEC 1')
    rp.tx_txt(f'ACQ:SOUR{canal}:GAIN HV')
    rp.tx_txt('ACQ:TRIG:LEV 0')
    rp.tx_txt('ACQ:START')
    
    time.sleep(0.01)
    
    rp.tx_txt(f'ACQ:SOUR{canal}:DATA:OLD:N? 1')
    
    data = rp.rx_txt()
    try:
        value = float(data.strip('{}\n\r').split(',')[-1])
        return value
    except ValueError:
        print(f"Erro na conversão do valor: {data}")
        return None

def calculate_normalized_position(x_diff, y_diff, sum_signal):
    # Normaliza as diferenças pelo sinal total (SUM)
    if sum_signal > 0.1:  # Evita divisão por zero
        x_norm = x_diff / sum_signal
        y_norm = y_diff / sum_signal
    else:
        x_norm = 0
        y_norm = 0
    
    # Limita os valores ao range [-1, 1]
    x_norm = max(min(x_norm, 1.0), -1.0)
    y_norm = max(min(y_norm, 1.0), -1.0)
    
    return x_norm, y_norm

def calculate_servo_angles(x_norm, y_norm):
    # Determina a direção predominante
    x_direction = 1 if x_norm > 0.1 else (-1 if x_norm < -0.1 else 0)
    y_direction = 1 if y_norm > 0.1 else (-1 if y_norm < -0.1 else 0)
    
    # Caso 1: Feixe à direita (Q2/Q3)
    if x_direction == 1 and abs(x_norm) > abs(y_norm):
        servo_x_angle = CENTER_ANGLE + (abs(x_norm) * MAX_ANGLE_RANGE)
        servo_y_angle = CENTER_ANGLE  # Mantém Y centralizado
    
    # Caso 2: Feixe à esquerda (Q1/Q4)  
    elif x_direction == -1 and abs(x_norm) > abs(y_norm):
        servo_x_angle = CENTER_ANGLE - (abs(x_norm) * MAX_ANGLE_RANGE)
        servo_y_angle = CENTER_ANGLE
    
    # Caso 3: Feixe no topo (Q1/Q2)
    elif y_direction == 1 and abs(y_norm) > abs(x_norm):
        servo_x_angle = CENTER_ANGLE
        servo_y_angle = CENTER_ANGLE + (abs(y_norm) * MAX_ANGLE_RANGE)
    
    # Caso 4: Feixe na base (Q3/Q4)
    elif y_direction == -1 and abs(y_norm) > abs(x_norm):
        servo_x_angle = CENTER_ANGLE
        servo_y_angle = CENTER_ANGLE - (abs(y_norm) * MAX_ANGLE_RANGE)
    
    # Caso misto (diagonal)
    else:
        servo_x_angle = CENTER_ANGLE + (x_norm * MAX_ANGLE_RANGE * 0.7)
        servo_y_angle = CENTER_ANGLE + (y_norm * MAX_ANGLE_RANGE * 0.7)
    
    return servo_x_angle, servo_y_angle


print("Lendo saídas do KPA101 (XDiff, YDiff, SUM). Ctrl+C para parar.")
try:
    while True:
        # Lê as três saídas do KPA101
        x_diff = read_single_value(3)   # XDiff (X+ - X-)
        y_diff = read_single_value(2)   # YDiff (Y+ - Y-)
        sum_signal = read_single_value(4)  # SUM (soma total)
        
        if all(v is not None for v in [x_diff, y_diff, sum_signal]):
            # Calcula a posição normalizada
            x_norm, y_norm = calculate_normalized_position(x_diff, y_diff, sum_signal)
            
            # Calcula o ângulo
            angle = calculate_angle(x_norm, y_norm)
            
            print(f"XDiff: {x_diff:.3f}V, YDiff: {y_diff:.3f}V")
            print(f"SUM: {sum_signal:.3f}V")
            print(f"XNorm: {x_norm:.3f}, YNorm: {y_norm:.3f}")
            print(f"Ângulo: {angle:.1f}°")
            print("-" * 40)
            
            # Controla o servo
            set_servo_angle(angle)
        
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nLeitura interrompida pelo usuário")

# Limpeza final
rp.tx_txt('ACQ:STOP')
print("Aquisição finalizada.")
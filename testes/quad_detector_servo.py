import redpitaya_scpi as scpi
import numpy as np
import time
import threading


# Configuração inicial
rp = scpi.scpi('10.42.0.25')  # IP da sua Red Pitaya

# Configurações do servo
CENTER_ANGLE = 90
MAX_ANGLE_RANGE = 30

SERVO_PIN1 = 'DIO0_N'
SERVO_PIN2 = 'DIO1_N'

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

def config_pin(servo_pin1, servo_pin2):
    rp.tx_txt(f'DIG:PIN:DIR OUT, {servo_pin1}')
    rp.tx_txt(f'DIG:PIN {servo_pin1}, 0')
    
    rp.tx_txt(f'DIG:PIN:DIR OUT, {servo_pin2}')
    rp.tx_txt(f'DIG:PIN {servo_pin2}, 0')
    time.sleep(0.1)

def move_servo_simultaneous(angle1, servo_pin1, angle2, servo_pin2):
    if angle1 < 0 or angle1 > 180 or angle2 < 0 or angle2 > 180:
        print("Erro: Ângulos devem estar entre 0 e 180 graus")
    
    # Cálculo dos pulsos para cada servo
    pulse_width1 = 500 + (angle1 / 180.0) * 2000
    pulse_width2 = 500 + (angle2 / 180.0) * 2000
    
    pulse_duration1 = pulse_width1 / 1000000.0
    pulse_duration2 = pulse_width2 / 1000000.0
    
    print(f"Movendo servo 1 para {angle1}° ({pulse_width1}μs) e servo 2 para {angle2}° ({pulse_width2}μs)")
    
    # Função para mover um servo individualmente (com threads)
    
    def move_single_servo(angle, pin, pulse_duration):
        rp.tx_txt(f'DIG:PIN {pin},1')
        time.sleep(pulse_duration)
        rp.tx_txt(f'DIG:PIN {pin},0')
    
    thread1 = threading.Thread(target=move_single_servo, args=(angle1, servo_pin1, pulse_duration1))
    thread2 = threading.Thread(target=move_single_servo, args=(angle2, servo_pin2, pulse_duration2))
    
    thread1.start()
    thread2.start()
    
    thread1.join()
    thread2.join()
    
    remaining_time = 0.02 - max(pulse_duration1, pulse_duration2)
    
    if remaining_time > 0:
        time.sleep(remaining_time)
    
    return True
    

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
            angle1, angle2 = calculate_servo_angles(x_norm, y_norm)
            
            if 0 <= angle1 <=180 and 0 <= angle2 <= 180:
                for _ in range(50):
                    move_servo_simultaneous(angle1, SERVO_PIN1, angle2, SERVO_PIN2)
            
            print(f"XDiff: {x_diff:.3f}V, YDiff: {y_diff:.3f}V")
            print(f"SUM: {sum_signal:.3f}V")
            print(f"XNorm: {x_norm:.3f}, YNorm: {y_norm:.3f}")
            print(f"Ângulo X: {angle1:.1f}°, Ângulo Y: {angle2:.1f}°")
            print("-" * 40)
            
            
        
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nLeitura interrompida pelo usuário")

# Limpeza final
rp.tx_txt('ACQ:STOP')
print("Aquisição finalizada.")
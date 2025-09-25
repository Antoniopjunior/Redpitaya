import redpitaya_scpi as scpi
import time
import math

# Configuração inicial
rp = scpi.scpi('10.42.0.25')  # IP da sua Red Pitaya

# Configurações do servo
SERVO_MIN_ANGLE = 0
SERVO_MAX_ANGLE = 180
SERVO_MIN_PULSE = 500
SERVO_MAX_PULSE = 2500

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
    """
    Calcula a posição normalizada usando as saídas diferenciais do KPA101
    XDiff e YDiff já são as diferenças (X+ - X-) e (Y+ - Y-)
    """
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

def calculate_angle(x_norm, y_norm):
    """
    Calcula o ângulo com base nos valores normalizados X e Y
    """
    # Calcula o ângulo em radianos
    angle_rad = math.atan2(y_norm, x_norm)
        
    # Converte para graus e ajusta para o range [0, 360]
    angle_deg = math.degrees(angle_rad) % 360
    
    # Mapeia para o range do servo (0-180 graus)
    servo_angle = angle_deg / 2 if angle_deg <= 180 else (angle_deg - 180) / 2
    
    return servo_angle

def set_servo_angle(angle):
    """
    Simula o controle do servo (implemente conforme seu hardware)
    """
    pulse_width = SERVO_MIN_PULSE + (angle / SERVO_MAX_ANGLE) * (SERVO_MAX_PULSE - SERVO_MIN_PULSE)
    print(f"Ângulo: {angle:.1f}° -> Pulso: {pulse_width:.0f}μs")

# Mapeamento dos canais para o KPA101
# CANAL 1: XDiff (saída diferencial X)
# CANAL 2: YDiff (saída diferencial Y) 
# CANAL 3: SUM (soma total)

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
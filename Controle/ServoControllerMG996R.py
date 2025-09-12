#!/usr/bin/env python3
import redpitaya_scpi as scpi
import time

# Conexões corretas:
# DIO -> Sinal (laranja) - Conectar na Pitaya
# 5V-6V -> Potência (vermelho) - Conectar em FONTE EXTERNA
# GND -> Solo (marrom) - Conectar no GND comum entre fonte e Pitaya

# Configuração
IP = "10.42.0.236"  # IP da Red Pitaya
rp = scpi.scpi(IP)
SERVO_PIN = 'DIO1_N'  # Pino de controle do servo

def check_power_warning():
    """Exibe avisos de segurança críticos para MG996R"""
    print("⚠️  AVISO CRÍTICO DE SEGURANÇA ⚠️")
    print("=" * 50)
    print("MG996R REQUER ALIMENTAÇÃO EXTERNA!")
    print("NÃO use a energia da Red Pitaya.")
    print("")
    print("CONEXÕES CORRETAS:")
    print("Sinal (Laranja)  -> DIO0_N (Pitaya)")
    print("VCC (Vermelho)   -> Fonte externa 5V-6V (>2A)")
    print("GND (Marrom)     -> GND comum (fonte + Pitaya)")
    print("")
    print("Danos permanentes podem ocorrer se")
    print("conectar incorretamente!")
    print("=" * 50)
    
    response = input("Confirmar que usa fonte externa (s/n): ").strip().lower()
    if response != 's':
        print("Operação cancelada por segurança")
        return False
    return True

def config_pin(servo_pin):
    """Configura o pino digital como saída"""
    rp.tx_txt(f'DIG:PIN:DIR OUT, {servo_pin}')
    rp.tx_txt(f'DIG:PIN {servo_pin}, 0')
    time.sleep(0.1)
    print(f"Pino {servo_pin} configurado como saída")

def calculate_pulse(angle):
    """Calcula a largura do pulso para o MG996R"""
    # ESPECIFICAÇÕES DO MG996R:
    # 0° = 1000μs (1.0ms)
    # 90° = 1500μs (1.5ms) 
    # 180° = 2000μs (2.0ms)
    # Frequência: 50Hz (período de 20ms)
    
    pulse_width = 1000 + (angle / 180.0) * 1000
    return pulse_width / 1000000.0  # converte para segundos

def move_servo(angle, servo_pin):
    """Move o servo MG996R para um ângulo específico (0-180 graus)"""
    if angle < 0 or angle > 180:
        print("Erro: Ângulo deve estar entre 0 e 180 graus")
        return False
    
    pulse_duration = calculate_pulse(angle)
    
    # Gera o pulso PWM
    rp.tx_txt(f'DIG:PIN {servo_pin},1')
    time.sleep(pulse_duration)
    rp.tx_txt(f'DIG:PIN {servo_pin},0')
    
    # Completa o período de 20ms
    time.sleep(0.02 - pulse_duration)
    
    return True

def test_servo_mg996r(servo_pin):
    """Teste específico para servo MG996R"""
    print("Iniciando teste do servo MG996R...")
    print("Monitorar a fonte de alimentação durante o teste!")
    
    # Testa posições principais do MG996R
    positions = [0, 45, 90, 135, 180, 90, 0]
    
    for pos in positions:
        print(f"→ Movendo para {pos}°")
        # Envia vários pulsos para garantir a posição
        for _ in range(50):
            move_servo(pos, servo_pin)
        time.sleep(0.5)  # Pequena pausa entre posições
    
    print("Teste concluído!")

def sweep_servo(servo_pin, start_angle=0, end_angle=180, step=5, delay=0.1):
    """Faz um movimento contínuo entre dois ângulos"""
    print(f"Varredura de {start_angle}° a {end_angle}°")
    
    # Movimento de ida
    for angle in range(start_angle, end_angle + step, step):
        if angle > end_angle:
            angle = end_angle
        move_servo(angle, servo_pin)
        time.sleep(delay)
    
    # Movimento de volta
    for angle in range(end_angle, start_angle - step, -step):
        if angle < start_angle:
            angle = start_angle
        move_servo(angle, servo_pin)
        time.sleep(delay)

def hold_position(angle, servo_pin):
    """Mantém o servo em uma posição específica"""
    if angle < 0 or angle > 180:
        print("Ângulo inválido")
        return
    
    print(f"Mantendo servo em {angle}° - Ctrl+C para parar")
    try:
        while True:
            move_servo(angle, servo_pin)
    except KeyboardInterrupt:
        print("Parando...")

def main():
    # Verificação de segurança crítica
    if not check_power_warning():
        return
    
    try:
        config_pin(SERVO_PIN)
        print("=" * 50)
        print("CONTROLE DO SERVO MG996R")
        print("=" * 50)
        print(f"IP: {IP}")
        print(f"Pino: {SERVO_PIN}")
        print("\nComandos:")
        print("  move    : Move para um ângulo específico")
        print("  test    : Teste automático")
        print("  sweep   : Varredura contínua")
        print("  hold    : Mantém posição")
        print("  center  : Centraliza (90°)")
        print("  stop    : Para o servo")
        print("  quit    : Sai")
        print("=" * 50)
        
        while True:
            cmd = input("\nComando: ").strip().lower()
            
            if cmd == 'quit':
                break
            elif cmd == 'test':
                test_servo_mg996r(SERVO_PIN)
            elif cmd == 'sweep':
                try:
                    start = int(input("Ângulo inicial (0-180): "))
                    end = int(input("Ângulo final (0-180): "))
                    if 0 <= start <= 180 and 0 <= end <= 180:
                        sweep_servo(SERVO_PIN, start, end)
                    else:
                        print("Ângulos devem ser 0-180")
                except ValueError:
                    print("Valor inválido")
            elif cmd == 'stop':
                rp.tx_txt(f'DIG:PIN {SERVO_PIN},0')
                print("Servo parado")
            elif cmd == 'center':
                for _ in range(50):
                    move_servo(90, SERVO_PIN)
                print("Servo centralizado em 90°")
            elif cmd == 'hold':
                try:
                    angle = float(input("Ângulo (0-180): "))
                    hold_position(angle, SERVO_PIN)
                except ValueError:
                    print("Ângulo inválido")
            elif cmd == 'move':
                try:
                    angle = float(input("Ângulo (0-180): "))
                    if 0 <= angle <= 180:
                        for _ in range(50):
                            move_servo(angle, SERVO_PIN)
                        print(f"Servo em {angle}°")
                    else:
                        print("Ângulo deve ser 0-180")
                except ValueError:
                    print("Valor inválido")
            else:
                print("Comando não reconhecido")
    
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário")
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        rp.tx_txt(f'DIG:PIN {SERVO_PIN},0')
        print("Programa finalizado")

if __name__ == '__main__':
    main()

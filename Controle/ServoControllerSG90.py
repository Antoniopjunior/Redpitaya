#!/usr/bin/env python3
import redpitaya_scpi as scpi
import time

# Conexões Servo -> Pitaya/Protoboard
# DIO -> Sinal (laranja)
# 5V -> Potência (vermelho)
# GND -> Solo (marrom)

# Configuração
IP = "10.42.0.25"  # IP da Red Pitaya
rp = scpi.scpi(IP)
SERVO_PIN = 'DIO1_N' # modificar dependendendo do pino 

# Configura o pino como saída
rp.tx_txt(f'DIG:PIN:DIR OUT, {SERVO_PIN}')
rp.tx_txt(f'DIG:PIN {SERVO_PIN},0')
time.sleep(0.1)

def move_servo(angle):
    """Move o servo SG90 para um ângulo específico (0-180 graus)"""
    if angle < 0 or angle > 180:
        print("Erro: Ângulo deve estar entre 0 e 180 graus")
        return False
    
    # ESPECIFICAÇÕES DO SG90:
    # 0° = 500μs (0.5ms)
    # 90° = 1500μs (1.5ms) 
    # 180° = 2500μs (2.5ms)
    # Frequência: 50Hz (período de 20ms)
    
    pulse_width = 500 + (angle / 180.0) * 2000
    pulse_duration = pulse_width / 1000000.0  # converte para segundos
    
    print(f"Movendo para {angle}° (pulso: {pulse_width}μs)")
    
    # Gera o pulso PWM
    rp.tx_txt(f'DIG:PIN {SERVO_PIN},1')
    time.sleep(pulse_duration)
    rp.tx_txt(f'DIG:PIN {SERVO_PIN},0')
    time.sleep(0.02 - pulse_duration)  # Completa o período de 20ms
    
    return True

def test_servo_sg90():
    """Teste específico para servo SG90"""
    print("Testando servo SG90 Tower Pro 9g...")
    
    # Testa posições principais do SG90
    positions = [0, 45, 90, 135, 180, 90, 0]
    
    for pos in positions:
        print(f"→ Movendo para {pos}°")
        # Envia vários pulsos para garantir a posição
        for _ in range(50):  # 50 pulsos (1 segundo)
            move_servo(pos)
        time.sleep(0.5)  # Pequena pausa entre posições

def hold_position(angle):
    """Mantém o servo em uma posição específica"""
    if angle < 0 or angle > 180:
        print("Ângulo inválido")
        return
    
    print(f"Mantendo servo em {angle}° - Ctrl+C para parar")
    try:
        while True:
            move_servo(angle)
    except KeyboardInterrupt:
        print("Parando...")

def main():
    try:
        print("=" * 50)
        print("CONTROLE DO SERVO ")
        print("=" * 50)
        print(f"IP: {IP}")
        print(f"Pino: {SERVO_PIN}")
        print("\nComandos:")
        print("  0-180  : Move para o ângulo")
        print("  test   : Teste automático")
        print("  hold   : Mantém posição")
        print("  center : Centraliza (90°)")
        print("  stop   : Para o servo")
        print("  quit   : Sai")
        print("=" * 50)
        
        while True:
            cmd = input("\nComando: ").strip().lower()
            
            if cmd == 'quit':
                break
            elif cmd == 'test':
                test_servo_sg90()
            elif cmd == 'stop':
                rp.tx_txt(f'DIG:PIN {SERVO_PIN},0')
                print("Servo parado")
            elif cmd == 'center':
                for _ in range(50):
                    move_servo(90)
                print("Servo centralizado em 90°")
            elif cmd == 'hold':
                try:
                    angle = float(input("Ângulo (0-180): "))
                    hold_position(angle)
                except ValueError:
                    print("Ângulo inválido")
            else:
                try:
                    angle = float(cmd)
                    if 0 <= angle <= 180:
                        for _ in range(50):
                            move_servo(angle)
                        print(f"Servo em {angle}°")
                    else:
                        print("Ângulo deve ser 0-180")
                except ValueError:
                    print("Comando inválido")
    
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário")
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        rp.tx_txt(f'DIG:PIN {SERVO_PIN},0')
        print("Programa finalizado")

if __name__ == '__main__':
    main()
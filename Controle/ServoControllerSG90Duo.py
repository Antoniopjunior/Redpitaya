#!/usr/bin/env python3
import redpitaya_scpi as scpi
import time
import threading

# Conexões Servo -> Pitaya/Protoboard
# DIO -> Sinal (laranja)test
# 5V -> Potência (vermelho)
# GND -> Solo (marrom)

# Configuração
IP = "10.42.0.236"  # IP da Red Pitaya
rp = scpi.scpi(IP)
SERVO_PIN1 = 'DIO0_N'
SERVO_PIN2 = 'DIO1_N'

def config_pin(servo_pin1, servo_pin2):
    rp.tx_txt(f'DIG:PIN:DIR OUT, {servo_pin1}')
    rp.tx_txt(f'DIG:PIN {servo_pin1}, 0')
    
    rp.tx_txt(f'DIG:PIN:DIR OUT, {servo_pin2}')
    rp.tx_txt(f'DIG:PIN {servo_pin2}, 0')
    time.sleep(0.1)

def move_servo_simultaneous(angle1, servo_pin1, angle2, servo_pin2):
    """Move ambos os servos simultaneamente para ângulos específicos (0-180 graus)"""
    if angle1 < 0 or angle1 > 180 or angle2 < 0 or angle2 > 180:
        print("Erro: Ângulos devem estar entre 0 e 180 graus")
        return False
    
    # Cálculo dos pulsos para cada servo
    pulse_width1 = 500 + (angle1 / 180.0) * 2000
    pulse_duration1 = pulse_width1 / 1000000.0
    
    pulse_width2 = 500 + (angle2 / 180.0) * 2000
    pulse_duration2 = pulse_width2 / 1000000.0
    
    print(f"Movendo servo 1 para {angle1}° ({pulse_width1}μs) e servo 2 para {angle2}° ({pulse_width2}μs)")
    
    # Função para mover um servo individualmente (usada com threads)
    def move_single_servo(angle, pin, pulse_duration):
        rp.tx_txt(f'DIG:PIN {pin},1')
        time.sleep(pulse_duration)
        rp.tx_txt(f'DIG:PIN {pin},0')
    
    # Cria threads para mover os servos simultaneamente
    thread1 = threading.Thread(target=move_single_servo, args=(angle1, servo_pin1, pulse_duration1))
    thread2 = threading.Thread(target=move_single_servo, args=(angle2, servo_pin2, pulse_duration2))
    
    # Inicia as threads
    thread1.start()
    thread2.start()
    
    # Aguarda ambas as threads terminarem
    thread1.join()
    thread2.join()
    
    # Completa o período de 20ms
    remaining_time = 0.02 - max(pulse_duration1, pulse_duration2)
    if remaining_time > 0:
        time.sleep(remaining_time)
    
    return True

def test_servo_sg90(servo_pin1, servo_pin2):
    """Teste específico para servos SG90"""
    print("Testando servos SG90 Tower Pro simultaneamente...")
    
    # Testa posições principais
    positions = [
        (0, 180),    # Extremos opostos
        (45, 135),   # Intermediários
        (90, 90),    # Centro
        (135, 45),   # Intermediários invertidos
        (180, 0),    # Extremos invertidos
        (90, 90)     # Volta ao centro
    ]
    
    for pos1, pos2 in positions:
        print(f"→ Movendo para {pos1}° e {pos2}°")
        # Envia vários pulsos para garantir a posição
        for _ in range(50):
            move_servo_simultaneous(pos1, servo_pin1, pos2, servo_pin2)
        time.sleep(0.5)

def hold_position_simultaneous(angle1, servo_pin1, angle2, servo_pin2):
    """Mantém ambos os servos em posições específicas"""
    if angle1 < 0 or angle1 > 180 or angle2 < 0 or angle2 > 180:
        print("Ângulos inválidos")
        return
    
    print(f"Mantendo servos em {angle1}° e {angle2}° - Ctrl+C para parar")
    try:
        while True:
            move_servo_simultaneous(angle1, servo_pin1, angle2, servo_pin2)
    except KeyboardInterrupt:
        print("Parando...")

def main():
    try:
        config_pin(SERVO_PIN1, SERVO_PIN2)
        print("=" * 50)
        print("CONTROLE SIMULTÂNEO DE DOIS SERVOS")
        print("=" * 50)
        print(f"IP: {IP}")
        print(f"Pinos: {SERVO_PIN1}, {SERVO_PIN2}")
        print("\nComandos:")
        print("  move    : Move para ângulos específicos")
        print("  test    : Teste automático")
        print("  hold    : Mantém posição")
        print("  center  : Centraliza ambos (90°)")
        print("  stop    : Para os servos")
        print("  quit    : Sai")
        print("=" * 50)
        
        while True:
            print("=" * 50)
            print("CONTROLE SIMULTÂNEO DE DOIS SERVOS")
            print("=" * 50)
            print(f"IP: {IP}")
            print(f"Pinos: {SERVO_PIN1}, {SERVO_PIN2}")
            print("\nComandos:")
            print("  move    : Move para ângulos específicos")
            print("  test    : Teste automático")
            print("  hold    : Mantém posição")
            print("  center  : Centraliza ambos (90°)")
            print("  stop    : Para os servos")
            print("  quit    : Sai")
            print("=" * 50)
            cmd = input("\nComando: ").strip().lower()
            
            if cmd == 'quit':
                break
            elif cmd == 'test':
                test_servo_sg90(SERVO_PIN1, SERVO_PIN2)
            elif cmd == 'stop':
                rp.tx_txt(f'DIG:PIN {SERVO_PIN1},0')
                rp.tx_txt(f'DIG:PIN {SERVO_PIN2},0')
                print("Servos parados")
            elif cmd == 'center':
                for _ in range(50):
                    move_servo_simultaneous(90, SERVO_PIN1, 90, SERVO_PIN2)
                print("Servos centralizados em 90°")
            elif cmd == 'hold':
                try:
                    angle1 = float(input("Ângulo servo 1 (0-180): "))
                    angle2 = float(input("Ângulo servo 2 (0-180): "))
                    hold_position_simultaneous(angle1, SERVO_PIN1, angle2, SERVO_PIN2)
                except ValueError:
                    print("Ângulo inválido")
            elif cmd == 'move':
                try:
                    angle1 = float(input("Ângulo servo 1 (0-180): "))
                    angle2 = float(input("Ângulo servo 2 (0-180): "))
                    if 0 <= angle1 <= 180 and 0 <= angle2 <= 180:
                        for _ in range(50):
                            move_servo_simultaneous(angle1, SERVO_PIN1, angle2, SERVO_PIN2)
                        print(f"Servo 1 em {angle1}° e Servo 2 em {angle2}°")
                    else:
                        print("Ângulos devem ser 0-180")
                except ValueError:
                    print("Valor inválido")
            else:
                print("Comando não reconhecido")
    
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário")
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        rp.tx_txt(f'DIG:PIN {SERVO_PIN1},0')
        rp.tx_txt(f'DIG:PIN {SERVO_PIN2},0')
        print("Programa finalizado")

if __name__ == '__main__':
    main()
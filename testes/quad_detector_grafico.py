import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import numpy as np
import time

# Colocar no modo monitor para uma medição mais precisa

# Configuração da Red Pitaya
rp = scpi.scpi('10.42.0.25')  # IP da sua Red Pitaya

def read_single_value(canal):
    """Lê um valor instantâneo do canal especificado da Red Pitaya"""
    try:
        # Configuração da aquisição
        rp.tx_txt('ACQ:DEC 1')          
        rp.tx_txt(f'ACQ:SOUR{canal}:GAIN HV')  
        rp.tx_txt('ACQ:TRIG:LEV 0')     
        rp.tx_txt('ACQ:START')          
        
        # Pequena pausa para estabilização
        time.sleep(0.01)
        rp.tx_txt(f'ACQ:SOUR{canal}:DATA:OLD:N? 1')
        
        # Recebe e processa o dado
        data = rp.rx_txt()
        
        # Remove caracteres especiais e converte para float
        value = float(data.strip('{}\n\r').split(',')[-1])
        return value
        
    except Exception as e:
        print(f"Erro na leitura do canal {canal}: {e}")
        return None

# Configuração do gráfico para o PDQ30C
DETECTOR_RADIUS = 1.0  # Valor normalizado

fig, ax = plt.subplots(figsize=(8, 7))
ax.set_xlim(-1.2, 1.2)
ax.set_ylim(-1.2, 1.2)
ax.set_aspect('equal')
ax.set_title("Beam Position - PDQ30C Quadrant Detector (Red Pitaya)")
ax.set_xlabel("X Position (normalized)")
ax.set_ylabel("Y Position (normalized)")  # CORRIGIDO: set_ylabel
ax.grid(True)

# Desenha o detector PDQ30C
detector = plt.Circle((0, 0), DETECTOR_RADIUS, fill=False, edgecolor='red', linewidth=2)
ax.add_patch(detector)

# Linhas de referência
ax.axhline(0, color='gray', linestyle='--', alpha=0.5)
ax.axvline(0, color='gray', linestyle='--', alpha=0.5)

# Ponto do feixe IR
beam_point, = ax.plot([0], [0], 'yo', markersize=15, label="IR Beam", markeredgecolor='black')

# Textos informativos
info_text = ax.text(0.02, 0.98, '', transform=ax.transAxes, va='top', 
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# Barra de intensidade SUM
sum_bar = ax.barh(-1.3, 0, height=0.1, color='blue', alpha=0.7)
ax.text(1.1, -1.3, 'SUM', ha='center', va='center')

plt.ion()
plt.show()

# Histórico do feixe
trajectory, = ax.plot([], [], 'g-', alpha=0.3, linewidth=1)
x_history = []
y_history = []
MAX_HISTORY = 50

print("Iniciando visualização do PDQ30C. Ctrl+C para parar.")

# Para melhor performance, mantenha referência à barra SUM
current_sum_bar = None

try:
    while True:
        # Leitura real dos sinais da Red Pitaya
        sum_voltage = read_single_value(4)  # Canal 4: SUM
        x_voltage = read_single_value(3)    # Canal 3: XDiff  
        y_voltage = read_single_value(2)    # Canal 2: YDiff
        
        if all(v is not None for v in [sum_voltage, x_voltage, y_voltage]):
            # Normalização (como no Kinesis)
            if abs(sum_voltage) > 0.1:  # Evita divisão por zero
                x_norm = x_voltage / sum_voltage
                y_norm = y_voltage / sum_voltage
            else:
                x_norm, y_norm = 0, 0
            
            # Limita ao raio do detector
            distance = np.sqrt(x_norm**2 + y_norm**2)
            if distance > DETECTOR_RADIUS:
                x_norm = x_norm * DETECTOR_RADIUS / distance
                y_norm = y_norm * DETECTOR_RADIUS / distance

            # Atualiza ponto do feixe
            beam_point.set_data([x_norm], [y_norm])
            
            # Atualiza histórico da trajetória
            x_history.append(x_norm)
            y_history.append(y_norm)
            if len(x_history) > MAX_HISTORY:
                x_history.pop(0)
                y_history.pop(0)
            trajectory.set_data(x_history, y_history)
            
            # Atualiza informações textuais
            info_text.set_text(
                f'SUM: {sum_voltage:.3f} V\n'
                f'XDiff: {x_voltage:.3f} V\n'
                f'YDiff: {y_voltage:.3f} V\n'
                f'XPos: {x_norm:.3f}\n'
                f'YPos: {y_norm:.3f}'
            )
            
            # Atualiza barra de SUM (forma mais eficiente)
            if current_sum_bar:
                current_sum_bar.remove()
            
            sum_bar_value = max(0, min(1.0, sum_voltage / 10.0))  # Normaliza para 0-10V
            current_sum_bar = ax.barh(-1.3, sum_bar_value * 2.4, height=0.1, color='blue', alpha=0.7)
            
            # Muda cor se SUM estiver fora da faixa ideal
            if sum_voltage < 0.5 or sum_voltage > 9.5:
                info_text.set_color('red')
                beam_point.set_color('red')  # Alerta visual
            else:
                info_text.set_color('black')
                beam_point.set_color('yellow')

            # Atualiza o display
            fig.canvas.draw_idle()  # Mais eficiente que draw()
            fig.canvas.flush_events()

        time.sleep(0.1)  # Taxa de atualização de ~10Hz

except KeyboardInterrupt:
    print("\nVisualização interrompida pelo usuário")

finally:
    # Limpeza final
    rp.tx_txt('ACQ:STOP')
    plt.ioff()
    plt.show(block=True)
    print("Aquisição finalizada.")
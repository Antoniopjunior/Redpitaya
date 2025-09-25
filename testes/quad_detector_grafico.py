import matplotlib.pyplot as plt
import redpitaya_scpi as scpi
import numpy as np
import time

# Configuração inicial da Red Pitaya

IP = ''
rp = scpi.scpi(IP)

#Definição das funções
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
        print(f'Erro na conversão do valor: {data}')
        return None

# Configuração do gráfico para o quad detector PDQ30C
DETECTOR_RADIUS = 1.0

fig, ax = plt.subplots(figsize=(6,6))
ax.set_xlim(-1.2, 1.2)
ax.set_ylim(-1.2, 1.2)
ax.set_aspect('equal')
ax.set_title("Beam Position - PDQ30C Quadrant Detector (IR)")
ax.set_xlabel("X position (normalized)")
ax.set_ylabel("Y position (normalized)")
ax.grid(True)

#Desenha o detector PDQ30C
detector = plt.Circle((0, 0), DETECTOR_RADIUS, fill=False, edgecolor='red', linewidth=2)
ax.add_patch(detector)

# Linhas de referência
ax.axhline(0, color='gray', linestyle='--', alpha=0.5)
ax.axvline(0, color='gray', linestyle='--', alpha=0.5)

#Ponto do feixe IR

beam_point = ax.plot([0], [0], 'yo', markersize=15, label='IR Beam', markeredgecolor='black')

# Textos informativos
info_text = ax.text(0.02, 0.98, '', transform=ax.transAxes, va='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.08))

# Barra de intensidade SUM
sum_bar = ax.barh(-1.3, 0, height=0.1, color='blue', alpha=0.7)
ax.text(1.1, -1.3, 'SUM', ha='center', va='center')

plt.ion()
plt.show()

#Histório co feixe (opcional)
trajectory, = ax.plot([], [], 'g-', alpha=0.3, linewidth=1)
x_history = []
y_history = []
MAX_HISTORY = 50

print('Iniciando visualização do detector PDQ30C')

try:
    while True:
        sum_voltage = read_single_value()
        x_voltage = read_single_value()
        y_voltage = read_single_value()
        
        if all(v is not None for v in [sum_voltage, x_voltage, y_voltage]):
            if abs(sum_voltage) > 0.1:
                
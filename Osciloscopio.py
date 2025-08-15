#!/usr/bin/python3
import time
import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

#testar com o AWG

IP = '10.42.0.25'
rp_s = scpi.scpi(IP)

# Parâmetros
tempo_total_segundos = 30  # Tempo total de execução
tempo_atualizacao = 0.2    # Intervalo entre atualizações (segundos)
buffer_size = 16384        # Tamanho do buffer de aquisição

# Configuração inicial
rp_s.__configure__()

# Configuração dos subplots
plt.ion()
fig, axs = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle('Osciloscópio - Red Pitaya', fontsize=16)
colors = ['r', 'b', 'g', 'm']
lines = []
time_axis = None

# Inicializa gráficos
for i in range(4):
    row, col = divmod(i, 2)
    line, = axs[row, col].plot([], [], colors[i], label=f'CH{i+1}')
    lines.append(line)
    axs[row, col].set_xlim(0, buffer_size)
    axs[row, col].set_ylim(-1.1, 1.1)  # Faixa de -1.1V a +1.1V
    axs[row, col].set_xlabel('Amostras')
    axs[row, col].set_ylabel('Tensão (V)')
    axs[row, col].grid(True)
    axs[row, col].legend()

plt.tight_layout()

start_time = time.time()
next_acquisition = start_time

try:
    while time.time() - start_time < tempo_total_segundos:
        if time.time() >= next_acquisition:
            
            print(f"\nAquisição em {datetime.now().strftime('%H:%M:%S')}")
            # Configura trigger no canal 1
            rp_s.tx_txt('ACQ:TRIG CH1_PE')
            
            # Inicia aquisição
            rp_s.tx_txt('ACQ:START')
            
            # Espera trigger
            trigger_timeout = time.time() + 0.5
            while True:
                rp_s.tx_txt('ACQ:TRIG:STAT?')
                if rp_s.rx_txt() == 'TD' or time.time() > trigger_timeout:
                    break
            
            # Adquire dados dos dois canais
            for ch in range(4):
                data = rp_s.ler_canal(ch+1)
                if time_axis is None:
                    time_axis = np.arange(len(data))
                lines[ch].set_data(time_axis, data)
            
            # Ajusta eixo x para mostrar apenas a parte relevante
            for i in range(4):
                row, col = divmod(i, 2)
                axs[row, col].relim()
                axs[row, col].autoscale_view(True, True, True)
            fig.canvas.flush_events()
            next_acquisition = time.time() + tempo_atualizacao
            
        plt.pause(0.01)

except KeyboardInterrupt:
    print("\nAquisição interrompida pelo usuário")
finally:
    rp_s.tx_txt('ACQ:STOP')
    rp_s.close()
    plt.ioff()
    plt.show()
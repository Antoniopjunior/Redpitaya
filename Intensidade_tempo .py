#!/usr/bin/python3
import time
# import sys
import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

IP = '169.254.56.223'
rp_s = scpi.scpi(IP)

# Parâmetros de aquisição
tempo_total_segundos = 10
intervalo_segundos = 1

# Configuração inicial do Red Pitaya
rp_s.__configure__()

# Listas para armazenar dados
tempos = []
intensidades = [[] for _ in range(4)]  # Lista de listas para os 4 canais
cores = ['b', 'g', 'r', 'm']  # Cores para cada canal
labels = ['Canal 1', 'Canal 2', 'Canal 3', 'Canal 4']
markers = ['o', 's', '^', 'd']  # Marcadores diferentes para cada canal

# Controle de tempo
start_time = time.time()
next_acquisition = start_time

while time.time() - start_time < tempo_total_segundos:
    now = time.time()

    if now >= next_acquisition:
        tempo_atual = time.time() - start_time

        # Dispara aquisição
        rp_s.tx_txt('ACQ:START')
        rp_s.tx_txt('ACQ:TRIG CH1_PE')

        # Espera trigger
        start_wait = time.time()
        while True:
            rp_s.tx_txt('ACQ:TRIG:STAT?')
            if rp_s.rx_txt() == 'TD' or (time.time() - start_wait) > 0.5:
                break

        # Espera buffer
        start_wait = time.time()
        while True:
            rp_s.tx_txt('ACQ:TRIG:FILL?')
            if rp_s.rx_txt() == '1' or (time.time() - start_wait) > 0.5:
                break

        # Lê e processa todos os 4 canais
        tempos.append(tempo_atual)
        rms_values = []

        for canal in range(4):
            sinal = rp_s.ler_canal(canal+1)
            sinal1 = np.array(sinal)
            intensidade = np.sqrt(np.mean(sinal1**2))
            intensidades[canal].append(intensidade)

        # Print no terminal
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Tempo: {tempo_atual:.2f}s | " +
              " | ".join([f"{labels[i]}: {intensidades[i][-1]:.4f}V RMS" for i in range(4)]))

        next_acquisition += intervalo_segundos

    time.sleep(0.01)

# Configuração do plot com 4 subgráficos
plt.figure(figsize=(14, 10))
plt.suptitle('Intensidade RMS em Função do Tempo - 4 Canais',
             fontsize=14, y=1.02)

for canal in range(4):
    plt.subplot(2, 2, canal+1)
    plt.plot(tempos, intensidades[canal],
             color=cores[canal],
             marker=markers[canal],
             linestyle='-',
             linewidth=1.5,
             markersize=5,
             label=labels[canal])

    # plt.ylim (0,0.5)
    plt.title(labels[canal], fontsize=12)
    plt.xlabel('Tempo (s)', fontsize=10)
    plt.ylabel('Intensidade (V RMS)', fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.7)

    # Ajuste automático dos limites do eixo y com margem de 10%
    if intensidades[canal]:
        global_max = max(max(channel) for channel in intensidades if channel)
        global_min = min(min(channel) for channel in intensidades if channel)
        margin = 0.1 * (global_max - global_min) if (global_max -
                                                     global_min) > 0 else 0.1
        plt.ylim(global_min - margin, global_max+margin)

    # Adiciona legenda
    plt.legend(loc='upper right', fontsize=9)

# Ajusta o layout para evitar sobreposição
plt.tight_layout()
plt.show()

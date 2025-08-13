#!/usr/bin/python3
import time
import sys
import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

IP = '169.254.56.223'
rp_s = scpi.scpi(IP)

# Parâmetros de aquisição
tempo_total_segundos = 10  # Tempo total de aquisição AQUI ONDE CONTROLA
intervalo_segundos = 0.000131    # Intervalo entre aquisições

# Configuração inicial do Red Pitaya
rp_s.__configure__()
<<<<<<< HEAD:plotandoladoalado.py
=======

>>>>>>> a31607d (organização da pasta de testes e padronização dos tipos dos documentos):testes/plotandoladoalado.py

# Listas para armazenar todos os dados
todas_as_leituras = []  # Armazena cada aquisição como um dicionário

# Inicia o temporizador
start_time = time.time()
ultimo_plot_time = start_time

while time.time() - start_time < tempo_total_segundos:
 if time.time() - ultimo_plot_time >= intervalo_segundos:
    ultimo_plot_time = time.time()  
    print(f"\nIniciando aquisição em {datetime.now().strftime('%H:%M:%S')}")
        
    # Dispara a aquisição
    rp_s.tx_txt('ACQ:START')
    rp_s.tx_txt('ACQ:TRIG CH2_PE')

    # Espera o trigger
    while True:
        rp_s.tx_txt('ACQ:TRIG:STAT?')
        if rp_s.rx_txt() == 'TD':
            break

    # Espera o buffer encher
    while True:
        rp_s.tx_txt('ACQ:TRIG:FILL?')
        if rp_s.rx_txt() == '1':
            break

    # Lê os dados dos 4 canais
    buff1 = rp_s.ler_canal(1)
    buff2 = rp_s.ler_canal(2)
    buff3 = rp_s.ler_canal(3)
    buff4 = rp_s.ler_canal(4)

    # Eixo de tempo (assumindo sample rate de 125 MHz)
    sample_rate=125e6
    ts = 1/sample_rate
    tempo = np.arange(len(buff1)) *ts
    print(f"Duração real do sinal: {tempo[-1]:.6f} segundos")
    print(f"Número de amostras: {len(buff1)}")

    # Armazena os dados da aquisição atual
    todas_as_leituras.append({
        "tempo": tempo,
        "buff1": buff1,
        "buff2": buff2,
        "buff3": buff3,
        "buff4": buff4,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    # Espera próximo ciclo
    time.sleep(intervalo_segundos)

print("Aquisição finalizada. Plotando gráficos...")

# Configuração da figura final (subplots lado a lado)
num_leituras = len(todas_as_leituras)
fig, axs = plt.subplots(1, num_leituras, figsize=(
    5 * num_leituras, 4), squeeze=False)
axs = axs.flatten()  # Transforma em uma lista plana de eixos

# Plota cada aquisição em um subplot separado
for i, leitura in enumerate(todas_as_leituras):
    ax = axs[i]
    ax.plot(leitura["tempo"], leitura["buff1"], 'r', label="CH1", linewidth=1)
    ax.plot(leitura["tempo"], leitura["buff2"], 'g', label="CH2", linewidth=1)
    ax.plot(leitura["tempo"], leitura["buff3"], 'b', label="CH3", linewidth=1)
    ax.plot(leitura["tempo"], leitura["buff4"], 'm', label="CH4", linewidth=1)

    ax.set_xlabel("Tempo (s)")
    ax.set_ylabel("Tensão (V)")
    ax.set_title(f"Aquisição {i+1}\n{leitura['timestamp']}")
    ax.grid(True)
    ax.legend()

plt.tight_layout()
plt.show()  # Exibe tudo de uma vez




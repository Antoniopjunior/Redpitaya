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
tempo_total_segundos = 5  # Tempo total de aquisição
intervalo_segundos = 1    # Intervalo entre aquisições

# Configuração inicial do Red Pitaya
rp_s.tx_txt('ACQ:RST')
rp_s.tx_txt('ACQ:DEC 1')
rp_s.tx_txt('ACQ:DATA:FORMAT ASCII')
rp_s.tx_txt('ACQ:DATA:UNITS VOLTS')
rp_s.tx_txt('ACQ:TRIG:LEV 0')
rp_s.tx_txt('ACQ:TRIG:DLY 0')

# Função para ler dados de um canal
def ler_canal(canal):
    rp_s.tx_txt(f'ACQ:SOUR{canal}:DATA?')
    raw = rp_s.rx_txt()
    raw = raw.strip('{}\n\r').replace("  ", "").split(',')
    return np.array(list(map(float, raw)))

# Listas para armazenar todos os dados
todas_as_leituras = []  # Armazena cada aquisição como um dicionário

# Inicia o temporizador
start_time = time.time()

while time.time() - start_time < tempo_total_segundos:
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
    buff1 = ler_canal(1)
    buff2 = ler_canal(2)
    buff3 = ler_canal(3)
    buff4 = ler_canal(4)

    # Eixo de tempo (assumindo sample rate de 125 MHz)
    ts = 1 / 125e6
    tempo = np.arange(len(buff1)) * ts

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
fig, axs = plt.subplots(1, num_leituras, figsize=(5 * num_leituras, 4), squeeze=False)
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
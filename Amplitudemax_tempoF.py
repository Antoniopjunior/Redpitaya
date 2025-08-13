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
tempo_total_segundos = 600
intervalo_segundos = 5

# Configuração inicial do Red Pitaya
rp_s.__configure__()

# Listas para armazenar todos os dados
todas_as_leituras = []
amplitudes_maximas = []  # Armazenará tuplas (tempo, max1, max2, max3, max4)
amplitudes_minimas = []
time_vec = []
# Controle de tempo
start_time = time.time()
next_acquisition = start_time

while time.time() - start_time < tempo_total_segundos:
    now = time.time()

    if now >= next_acquisition:
        tempo_atual = time.time() - start_time
        print(f"\nAquisição em {datetime.now().strftime('%H:%M:%S')}")

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

        # Lê dados
        buff1 = rp_s.ler_canal(1)
        buff2 = rp_s.ler_canal(2)
        buff3 = rp_s.ler_canal(3)
        buff4 = rp_s.ler_canal(4)

        # Eixo de tempo
        sample_rate = 125e6
        ts = 1/sample_rate
        tempo = np.arange(len(buff1)) * ts

        # Calcula amplitudes máximas
        max1, max2, max3, max4 = np.max(buff1), np.max(
            buff2), np.max(buff3), np.max(buff4)
        min1, min2, min3, min4 = np.min(buff1), np.min(
            buff2), np.min(buff3), np.min(buff4)
        time_vec.append(tempo_atual)
        amplitudes_maximas.append((max1, max2, max3, max4))
        amplitudes_minimas.append((min1, min2, min3, min4))

        todas_as_leituras.append({
            "tempo": tempo,
            "buff1": buff1,
            "buff2": buff2,
            "buff3": buff3,
            "buff4": buff4,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

        next_acquisition += intervalo_segundos
        remaining = tempo_total_segundos - (time.time() - start_time)
        print(
            f"Próxima em: {intervalo_segundos}s | Restante: {remaining:.2f}s")
        print(
            f"Amplitudes máximas - CH1: {max1:.2f}V, CH2: {max2:.2f}V, CH3: {max3:.2f}V, CH4: {max4:.2f}V")

    time.sleep(0.01)


# Plotagem com sobreposição simples
print(f"\nTotal de aquisições: {len(todas_as_leituras)}")
plt.figure(figsize=(12, 10))

# Subplot 1: Sobreposição das formas de onda
plt.subplot(2, 1, 1)
cores = ['r', 'g', 'b', 'm']

for i, leitura in enumerate(todas_as_leituras):
    plt.plot(leitura["tempo"], leitura["buff1"], color=cores[0],
             label=f"CH1 (aq.{i+1})" if i == 0 else "", linewidth=1)
    plt.plot(leitura["tempo"], leitura["buff2"], color=cores[1],
             label=f"CH2 (aq.{i+1})" if i == 0 else "", linewidth=1)
    plt.plot(leitura["tempo"], leitura["buff3"], color=cores[2],
             label=f"CH3 (aq.{i+1})" if i == 0 else "", linewidth=1)
    plt.plot(leitura["tempo"], leitura["buff4"], color=cores[3],
             label=f"CH4 (aq.{i+1})" if i == 0 else "", linewidth=1)


global_max = np.max(amplitudes_maximas)
global_min = np.min(amplitudes_minimas)
margin = 0.1
# Exemplo: escala Y fixa de 0V a 5V
plt.ylim(global_min - margin, global_max+margin)


plt.title("Sobreposição de todas as aquisições")
plt.grid(True)
plt.legend()
plt.ylabel("Tensão (V)")

# Subplot 2: Amplitudes máximas vs tempo
plt.subplot(2, 1, 2)
tempos = [x for x in time_vec]
max1 = [x[0] for x in amplitudes_maximas]
max2 = [x[1] for x in amplitudes_maximas]
max3 = [x[2] for x in amplitudes_maximas]
max4 = [x[3] for x in amplitudes_maximas]

plt.plot(tempos, max1, 'r-o', label="CH1 Max")
plt.plot(tempos, max2, 'g-o', label="CH2 Max")
plt.plot(tempos, max3, 'b-o', label="CH3 Max")
plt.plot(tempos, max4, 'm-o', label="CH4 Max")

# plt.xlim(0, tempo_total_segundos)
# plt.ylim(0, 1)

plt.title("Amplitude máxima em função do tempo")
plt.xlabel("Tempo (s)")
plt.ylabel("Amplitude máxima (V)")
plt.grid(True)
plt.legend()


plt.tight_layout()
plt.show()

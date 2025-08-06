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
tempo_total_segundos = 30
intervalo_segundos = 2

# Configuração inicial do Red Pitaya
rp_s.tx_txt('ACQ:RST')
rp_s.tx_txt('ACQ:DEC 1')
rp_s.tx_txt('ACQ:DATA:FORMAT ASCII')
rp_s.tx_txt('ACQ:DATA:UNITS VOLTS')
rp_s.tx_txt('ACQ:TRIG:LEV 0')
rp_s.tx_txt('ACQ:TRIG:DLY 0')

def ler_canal(canal):
    rp_s.tx_txt(f'ACQ:SOUR{canal}:DATA?')
    raw = rp_s.rx_txt()
    raw = raw.strip('{}\n\r').replace("  ", "").split(',')
    return np.array(list(map(float, raw)))

# Listas para armazenar todos os dados
todas_as_leituras = []

# Controle de tempo
start_time = time.time()
next_acquisition = start_time

while time.time() - start_time < tempo_total_segundos:
    now = time.time()
    
    if now >= next_acquisition:
        print(f"\nAquisição em {datetime.now().strftime('%H:%M:%S')}")
        
        # Dispara aquisição
        rp_s.tx_txt('ACQ:START')
        rp_s.tx_txt('ACQ:TRIG CH2_PE')

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
        buff1 = ler_canal(1)
        buff2 = ler_canal(2)
        buff3 = ler_canal(3)
        buff4 = ler_canal(4)

        # Eixo de tempo
        sample_rate = 125e6
        ts = 1/sample_rate
        tempo = np.arange(len(buff1)) * ts
        
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
        print(f"Próxima em: {intervalo_segundos}s | Restante: {remaining:.2f}s")

    time.sleep(0.01)

# Plotagem com sobreposição simples
print(f"\nTotal de aquisições: {len(todas_as_leituras)}")
plt.figure(figsize=(10, 6))

# Cores originais para cada canal
cores = ['r', 'g', 'b', 'm']

for i, leitura in enumerate(todas_as_leituras):
    plt.plot(leitura["tempo"], leitura["buff1"], color=cores[0], label=f"CH1 (aq.{i+1})" if i == 0 else "", linewidth=1)
    plt.plot(leitura["tempo"], leitura["buff2"], color=cores[1], label=f"CH2 (aq.{i+1})" if i == 0 else "", linewidth=1)
    plt.plot(leitura["tempo"], leitura["buff3"], color=cores[2], label=f"CH3 (aq.{i+1})" if i == 0 else "", linewidth=1)
    plt.plot(leitura["tempo"], leitura["buff4"], color=cores[3], label=f"CH4 (aq.{i+1})" if i == 0 else "", linewidth=1)

plt.title("Sobreposição de todas as aquisições")
plt.grid(True)
plt.legend()  # Mostra apenas uma legenda por canal
plt.tight_layout()
plt.show()
#!/usr/bin/python3
import time
import sys
import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

IP = '169.254.56.25'
rp_s = scpi.scpi(IP)

# Parâmetros de aquisição (MODIFICADOS PARA TESTE)
tempo_total_segundos = 10  # 6 segundos totais
intervalo_segundos = 5    # 1 segundo entre aquisições TEM QUE SER UM NOME DIVISIVEL PELO DE CIMA SEU ENERGUMINO

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

# Controle de tempo PRECISO
start_time = time.time()
next_acquisition = start_time

while time.time() - start_time < tempo_total_segundos:
    now = time.time()
    
    if now >= next_acquisition:
        print(f"\nAquisição em {datetime.now().strftime('%H:%M:%S')}")
        
        # Dispara aquisição
        rp_s.tx_txt('ACQ:START')
        rp_s.tx_txt('ACQ:TRIG CH2_PE')

        # Espera trigger (MODIFICADO para não travar)
        start_wait = time.time()
        while True:
            rp_s.tx_txt('ACQ:TRIG:STAT?')
            if rp_s.rx_txt() == 'TD' or (time.time() - start_wait) > 0.5:
                break

        # Espera buffer (MODIFICADO)
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
        
        # Atualiza o próximo horário DE FORMA PRECISA
        next_acquisition += intervalo_segundos
        
        # Feedback
        remaining = tempo_total_segundos - (time.time() - start_time)
        print(f"Próxima em: {intervalo_segundos}s | Restante: {remaining:.2f}s")

    # Pequena pausa para não sobrecarregar CPU
    time.sleep(0.01)

# Plotagem (igual ao seu original)
print(f"\nTotal de aquisições: {len(todas_as_leituras)}")
fig, axs = plt.subplots(1, len(todas_as_leituras), figsize=(5*len(todas_as_leituras), 4), squeeze=False)
axs = axs.flatten()

for i, leitura in enumerate(todas_as_leituras):
    ax = axs[i]
    ax.plot(leitura["tempo"], leitura["buff1"], 'r', label="CH1", linewidth=1)
    ax.plot(leitura["tempo"], leitura["buff2"], 'g', label="CH2", linewidth=1)
    ax.plot(leitura["tempo"], leitura["buff3"], 'b', label="CH3", linewidth=1)
    ax.plot(leitura["tempo"], leitura["buff4"], 'm', label="CH4", linewidth=1)
    
    ax.set_title(f"Aq.{i+1} @ {leitura['timestamp']}")
    ax.grid(True)
    if i == 0: ax.legend()

plt.tight_layout()
plt.show()
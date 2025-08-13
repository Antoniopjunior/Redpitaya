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
tempo_total_segundos = 60
intervalo_segundos = 2

# Configuração inicial do Red Pitaya
rp_s.__configure__()

# Listas para armazenar todos os dados
todas_as_leituras = []
amplitudes_maximas = []  # Armazenará tuplas (tempo, max1, max2, max3, max4)

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
        amplitudes_maximas.append((tempo_atual, max1, max2, max3, max4))

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

# Processamento FFT e plotagem
print(f"\nTotal de aquisições: {len(todas_as_leituras)}")
plt.figure(figsize=(12, 10))

# Subplot 1: Espectro de frequência
plt.subplot(2, 1, 1)
cores = ['r', 'g', 'b', 'm']
sample_rate = 125e6  # Taxa de amostragem da Red Pitaya

for i, leitura in enumerate(todas_as_leituras):
    # Calcula FFT para cada canal
    n = len(leitura["buff1"])
    freq = np.fft.rfftfreq(n, d=1/sample_rate)

    fft1 = np.abs(np.fft.rfft(leitura["buff1"])) / n * 2
    fft2 = np.abs(np.fft.rfft(leitura["buff2"])) / n * 2
    fft3 = np.abs(np.fft.rfft(leitura["buff3"])) / n * 2
    fft4 = np.abs(np.fft.rfft(leitura["buff4"])) / n * 2

    plt.semilogy(
        freq/1e6, fft1, color=cores[0], alpha=0.7, label=f"CH1 (aq.{i+1})" if i == 0 else "")
    plt.semilogy(
        freq/1e6, fft2, color=cores[1], alpha=0.7, label=f"CH2 (aq.{i+1})" if i == 0 else "")
    plt.semilogy(
        freq/1e6, fft3, color=cores[2], alpha=0.7, label=f"CH3 (aq.{i+1})" if i == 0 else "")
    plt.semilogy(
        freq/1e6, fft4, color=cores[3], alpha=0.7, label=f"CH4 (aq.{i+1})" if i == 0 else "")

plt.title("Espectro de frequência das aquisições")
plt.grid(True)
plt.legend()
plt.ylabel("Amplitude (V)")
plt.xlabel("Frequência (MHz)")
plt.xlim(0, sample_rate/2e6)


# Subplot 2: Amplitude máxima por frequência ao longo do tempo
plt.subplot(2, 1, 2)

# Prepara dados para cada canal
freqs = None  # Inicializa como None
max_amps = {1: [], 2: [], 3: [], 4: []}

for leitura in todas_as_leituras:
    n = len(leitura["buff1"])
    freq = np.fft.rfftfreq(n, d=1/sample_rate)
    if freqs is None:  # Verificação correta para array não inicializado
        freqs = freq/1e6  # Armazena as frequências apenas uma vez (em MHz)

    # Calcula FFT para cada canal e armazena a amplitude máxima
    fft1 = np.abs(np.fft.rfft(leitura["buff1"])) / n * 2
    fft2 = np.abs(np.fft.rfft(leitura["buff2"])) / n * 2
    fft3 = np.abs(np.fft.rfft(leitura["buff3"])) / n * 2
    fft4 = np.abs(np.fft.rfft(leitura["buff4"])) / n * 2

    max_amps[1].append(np.max(fft1))
    max_amps[2].append(np.max(fft2))
    max_amps[3].append(np.max(fft3))
    max_amps[4].append(np.max(fft4))

# Tempo das aquisições
tempos = [x[0] for x in amplitudes_maximas]

plt.plot(tempos, max_amps[1], 'r-o', label="CH1 Max FFT")
plt.plot(tempos, max_amps[2], 'g-o', label="CH2 Max FFT")
plt.plot(tempos, max_amps[3], 'b-o', label="CH3 Max FFT")
plt.plot(tempos, max_amps[4], 'm-o', label="CH4 Max FFT")

plt.title("Amplitude máxima no domínio da frequência em função do tempo")
plt.xlabel("Tempo (s)")
plt.ylabel("Amplitude máxima na FFT (V)")
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()

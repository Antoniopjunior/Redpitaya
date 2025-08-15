#!/usr/bin/python3
import time
import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

IP = '10.42.0.25'
rp_s = scpi.scpi(IP)

# Parâmetros
tempo_total_segundos = 20
intervalo_segundos = 1
sample_rate = 125e6
ts = 1 / sample_rate

#Configuração inicial do RBW
RBW = 100e3 # edite aqui o valor do rbw
MIN_RBW = 1e3 # 1 kHz - Mínimo RBW
MAX_RBW = 1e6 # 1 MHz - Máximo RBW

# Configuração inicial
rp_s.__configure__()

# Configuração dos subplots
plt.ion()
fig, axs = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle(f'Spectrum Analyzer - 4 Canais\n RBW: {RBW/1e3:.1f} kHz', fontsize=16)
colors = ['r', 'g', 'b', 'm']
lines = []
frequencias = None

# Inicializa gráficos
for i in range(4):
    row, col = divmod(i, 2)
    line, = axs[row, col].plot([], [], colors[i], label=f'CH{i+1}')
    lines.append(line)
    axs[row, col].set_xlim(0, sample_rate/2/1e6)  # MHz
    axs[row, col].set_xticks(np.arange(0, sample_rate/2/1e6, 5))
    axs[row, col].set_ylim(-80, 10)
    axs[row, col].set_xlabel('Frequência (MHz)')
    axs[row, col].set_ylabel('Amplitude (dB)')
    axs[row, col].grid(True)
    axs[row, col].legend()

plt.tight_layout()

def calcular_fft(sinal, rbw):
    n = len(sinal)
    
    # Calcula o tamanho necessário da FFT para atingir a RBW desejada
    n_rbw = int(sample_rate / rbw)
    n_rbw = min(n_rbw, n) #não pode ser maior que o buffer
    n_rbw = max(n_rbw, 2) #pelo menos 2 pontos
    
    #Recorta o sinal para o novo tamanho
    sinal_recortado = sinal[:n_rbw] 
    
    window = np.hanning(n_rbw)
    fft_result = np.fft.fft(sinal_recortado * window)
    fft_freq = np.fft.fftfreq(n_rbw, d=ts)[:n_rbw//2]
    fft_db = 20 * np.log10(np.abs(fft_result[:n_rbw//2]) + 1e-10)
    
    return fft_freq, fft_db



start_time = time.time()
next_acquisition = start_time

try:
    while time.time() - start_time < tempo_total_segundos:
        if time.time() >= next_acquisition:
            print(f"\nAquisição em {datetime.now().strftime('%H:%M:%S')}")
            
            rp_s.tx_txt('ACQ:START')
            rp_s.tx_txt('ACQ:TRIG CH1_PE')
            
            # Espera trigger
            trigger_timeout = time.time() + 0.5
            while True:
                rp_s.tx_txt('ACQ:TRIG:STAT?')
                if rp_s.rx_txt() == 'TD' or time.time() > trigger_timeout:
                    break
            
            # Processa todos os 4 canais
            for ch in range(4):
                data = rp_s.ler_canal(ch+1)
                
                freq, fft_db = calcular_fft(data, RBW)
                if frequencias is None:
                    frequencias = freq
                
                lines[ch].set_data(freq/1e6, fft_db)  # Converte para MHz
            
            fig.canvas.flush_events()
            next_acquisition += intervalo_segundos
            
        plt.pause(0.05)

except KeyboardInterrupt:
    print("\nAquisição interrompida pelo usuário")
finally:
    rp_s.tx_txt('ACQ:STOP')
    rp_s.close()
    plt.ioff()
    plt.show()
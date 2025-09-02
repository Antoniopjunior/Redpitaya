#!/usr/bin/python3
import time
import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import RedpitayaMath as rpmath

IP = '10.42.0.25' # SO Windows: 169.254.56.223 | SO Linux Ubuntu: 10.4.0.25
rp_s = scpi.scpi(IP)

# Parâmetros
tempo_total_segundos = 10
intervalo_segundos = 1
sample_rate = 125e6
ts = 1 / sample_rate
canal = 1 # digite o n° (de 1 a 4) do canal desejado

# Configuração inicial do RBW e atenuacao
RBW = 100e3  # 100 kHz de RBW inicial
MIN_RBW = 1e3  # 1 kHz - mínimo RBW
MAX_RBW = 1e6  # 1 MHz - máximo RBW
atenuacao = 0 # digite a atenuação desejada
MIN_ATT = 0
MAX_ATT = 20

# Configuração inicial
rp_s.__configure__()

# Configuração do gráfico
plt.ion()
fig, ax = plt.subplots(figsize=(15, 7))
fig.suptitle(f'Spectrum Analyzer | Canal {canal}\nRBW: {RBW/1e3:.1f} kHz| Atenuação: {atenuacao}', fontsize=16)

# Linha do espectro
line, = ax.plot([], [], 'b', label='Espectro')
ax.set_xlim(0, sample_rate/2/1e6)  # MHz
ax.set_xticks(np.arange(0, sample_rate/2/1e6, 5))
ax.set_ylim(-80, 80)
ax.set_xlabel('Frequência (MHz)')
ax.set_ylabel('Amplitude (dB)')
ax.grid(True)
ax.legend()

plt.tight_layout()

start_time = time.time()
next_acquisition = start_time

try:
    
    rp_s.set_attenuation(canal, atenuacao) # aplicação da atenuação
    
    while time.time() - start_time < tempo_total_segundos:
        if time.time() >= next_acquisition:
            print(f"\nAquisição em {datetime.now().strftime('%H:%M:%S')} - RBW: {RBW/1e3:.1f} kHz")
            
            rp_s.tx_txt('ACQ:START')
            rp_s.tx_txt(f'ACQ:TRIG CH{canal}_PE')
            
            # Espera trigger
            trigger_timeout = time.time() + 0.5
            while True:
                rp_s.tx_txt('ACQ:TRIG:STAT?')
                if rp_s.rx_txt() == 'TD' or time.time() > trigger_timeout:
                    break
            
            # Adquire dados do canal
            data = rp_s.ler_canal(canal)
            
            # Calcula FFT com RBW atual
            freq, fft_db = rpmath.calcular_fft(data, RBW)
            
            # Atualiza gráfico
            line.set_data(freq/1e6, fft_db)
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
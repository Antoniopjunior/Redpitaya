#!/usr/bin/python3
import time
import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

IP = '10.42.0.25'
rp_s = scpi.scpi(IP)

# Parâmetros
tempo_total_segundos = 30  # Tempo total de execução
tempo_atualizacao = 0.2    # Intervalo entre atualizações (segundos)
buffer_size = 16384        # Tamanho do buffer de aquisição
sample_rate = 125e6        # Taxa de amostragem
ts = 1 / sample_rate       # Período de amostragem

# Configuração RBW
RBW = 100e3  # Resolution Bandwidth inicial (100 kHz)
MIN_RBW = 1e3  # 1 kHz
MAX_RBW = 1e6  # 1 MHz

# Configuração inicial
rp_s.__configure__()

# Configuração da interface
plt.ion()
fig = plt.figure(figsize=(16, 12))
fig.suptitle(f'Osciloscópio e Spectrum Analyzer - RBW: {RBW/1e3:.1f} kHz', fontsize=16)

# Cria subplots para cada canal 
axs_osc = []  # Para os gráficos do osciloscópio
axs_spec = [] # Para os gráficos do spectrum analyzer
lines_osc = []
lines_spec = []

for i in range(4):
    # Gráfico do osciloscópio
    ax_osc = plt.subplot(4, 2, 2*i+1)
    line_osc, = ax_osc.plot([], [], 'b', label=f'CH{i+1} - Temporal')
    ax_osc.set_xlim(0, buffer_size)
    ax_osc.set_ylim(-1.1, 1.1)
    ax_osc.set_ylabel('Tensão (V)')
    ax_osc.grid(True)
    ax_osc.legend()
    
    # Gráfico do spectrum analyzer
    ax_spec = plt.subplot(4, 2, 2*i+2)
    line_spec, = ax_spec.plot([], [], 'r', label=f'CH{i+1} - Frequência')
    ax_spec.set_xlim(0, sample_rate/2/1e6)  # MHz
    ax_spec.set_ylim(-80, 10)
    ax_spec.set_ylabel('Amplitude (dB)')
    ax_spec.grid(True)
    ax_spec.legend()
    
    axs_osc.append(ax_osc)
    axs_spec.append(ax_spec)
    lines_osc.append(line_osc)
    lines_spec.append(line_spec)

plt.tight_layout()

def calcular_fft(sinal, rbw):
    """Calcula a FFT com RBW específica"""
    n = len(sinal)
    n_rbw = int(sample_rate / rbw)
    n_rbw = min(n_rbw, n)
    n_rbw = max(n_rbw, 2)
    
    sinal_recortado = sinal[:n_rbw]
    window = np.hanning(n_rbw)
    fft_result = np.fft.fft(sinal_recortado * window)
    fft_freq = np.fft.fftfreq(n_rbw, d=ts)[:n_rbw//2]
    fft_db = 20 * np.log10(np.abs(fft_result[:n_rbw//2]) + 1e-10)
    return fft_freq, fft_db, sinal_recortado


def atualizar_rbw(nova_rbw):
    """Atualiza o valor de RBW e o título do gráfico"""
    global RBW
    RBW = max(MIN_RBW, min(nova_rbw, MAX_RBW))
    fig.suptitle(f'Osciloscópio e Spectrum Analyzer - RBW: {RBW/1e3:.1f} kHz', fontsize=16)
    print(f"\nRBW alterada para: {RBW/1e3:.1f} kHz")

start_time = time.time()
next_acquisition = start_time

try:
    print("Iniciando aquisição... Pressione Ctrl+C para parar")
    print("Digite 'rbw X' para alterar a RBW para X kHz (ex: 'rbw 10')")
    
    while time.time() - start_time < tempo_total_segundos:
        if time.time() >= next_acquisition:
            # Configura trigger
            rp_s.tx_txt('ACQ:TRIG CH1_PE')
            rp_s.tx_txt('ACQ:START')
            
            # Espera trigger
            trigger_timeout = time.time() + 0.5
            while True:
                rp_s.tx_txt('ACQ:TRIG:STAT?')
                if rp_s.rx_txt() == 'TD' or time.time() > trigger_timeout:
                    break
            
            # Processa todos os 4 canais
            for ch in range(4):
                data = rp_s.ler_canal(ch+1)
                time_axis = np.arange(len(data))
                
                # Atualiza osciloscópio
                lines_osc[ch].set_data(time_axis, data)
                axs_osc[ch].relim()
                axs_osc[ch].autoscale_view(True, True, True)
                
                # Atualiza spectrum analyzer com RBW atual
                freq, fft_db, _ = calcular_fft(data, RBW)
                lines_spec[ch].set_data(freq/1e6, fft_db)
                axs_spec[ch].relim()
                axs_spec[ch].autoscale_view(True, True, True)
            
            fig.canvas.flush_events()
            next_acquisition = time.time() + tempo_atualizacao
        
        # Verifica se há comando do usuário
        if plt.waitforbuttonpress(0.01):
            cmd = input("\nComando (rbw X): ").strip()
            if cmd.startswith('rbw'):
                try:
                    nova_rbw = float(cmd.split()[1]) * 1e3
                    atualizar_rbw(nova_rbw)
                except:
                    print("Formato inválido. Use 'rbw X' (ex: 'rbw 10')")

except KeyboardInterrupt:
    print("\nAquisição interrompida pelo usuário")
finally:
    rp_s.tx_txt('ACQ:STOP')
    rp_s.close()
    plt.ioff()
    plt.show()
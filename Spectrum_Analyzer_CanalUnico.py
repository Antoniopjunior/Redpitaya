#!/usr/bin/python3
import time
import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

IP = '10.42.0.25'
rp_s = scpi.scpi(IP)

# Parâmetros
tempo_total_segundos = 10
intervalo_segundos = 1
sample_rate = 125e6
ts = 1 / sample_rate
canal = 1  # digite o n° (de 1 a 4) do canal desejado

# Configuração inicial do RBW e atenuacao
RBW = 100e3  # 100 kHz de RBW inicial
MIN_RBW = 1e3  # 1 kHz - mínimo RBW
MAX_RBW = 1e6  # 1 MHz - máximo RBW
atenuacao = 0  # digite a atenuação desejada
MIN_ATT = 0
MAX_ATT = 20

# Configuração inicial
rp_s.__configure__()

# Configuração do gráfico
plt.ion()
fig, ax = plt.subplots(figsize=(15, 7))
fig.suptitle(f'Spectrum Analyzer | Canal {canal}\nRBW: {RBW/1e3:.1f} kHz | Atenuação: {atenuacao}dB', fontsize=16)

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

def calcular_fft(sinal, rbw):
    n = len(sinal)
    
    # Calcula o tamanho necessário da FFT para atingir a RBW desejada
    n_rbw = int(sample_rate / rbw)
    n_rbw = min(n_rbw, n)  # Não pode ser maior que o buffer
    n_rbw = max(n_rbw, 2)  # Pelo menos 2 pontos
    
    # Recorta o sinal para o novo tamanho
    sinal_recortado = sinal[:n_rbw]
    
    window = np.hanning(n_rbw)
    fft_result = np.fft.fft(sinal_recortado * window)
    fft_freq = np.fft.fftfreq(n_rbw, d=ts)[:n_rbw//2]
    fft_db = 20 * np.log10(np.abs(fft_result[:n_rbw//2]) + 1e-10)
    
    return fft_freq, fft_db

def set_attenuation(channel, att_db):
    """Configura a atenuação para um canal específico"""
    global atenuacao
    if MIN_ATT <= att_db <= MAX_ATT:
        rp_s.tx_txt(f'ACQ:SOUR{channel}:GAIN {"LV" if att_db == 0 else "HV"}')
        atenuacao = att_db
        fig.suptitle(f'Spectrum Analyzer | Canal {canal}\nRBW: {RBW/1e3:.1f} kHz | Atenuação: {atenuacao}dB', fontsize=16)
        print(f"Atenuação do CH{channel} configurada para {att_db}dB")
        return True
    else:
        print(f"Atenuação {att_db}dB não suportada. Use entre {MIN_ATT} e {MAX_ATT} dB")
        return False

def ler_canal(canal):
    """Lê os dados de um canal específico"""
    rp_s.tx_txt(f'ACQ:SOUR{canal}:DATA?')
    data_str = rp_s.rx_txt().strip('{}\n\r').replace("  ", "").split(',')
    return np.array(list(map(float, data_str)))

start_time = time.time()
next_acquisition = start_time

try:
    print(f"Iniciando aquisição no canal {canal}...")
    print("Pressione Ctrl+C para parar")
    print("Durante a execução, digite 'att X' para alterar a atenuação")
    
    # APLICA A ATENUAÇÃO INICIAL
    set_attenuation(canal, atenuacao)
    
    while time.time() - start_time < tempo_total_segundos:
        if time.time() >= next_acquisition:
            print(f"\nAquisição em {datetime.now().strftime('%H:%M:%S')} - RBW: {RBW/1e3:.1f} kHz - Atenuação: {atenuacao}dB")
            
            rp_s.tx_txt('ACQ:START')
            rp_s.tx_txt(f'ACQ:TRIG CH{canal}_PE')
            
            # Espera trigger
            trigger_timeout = time.time() + 0.5
            while True:
                rp_s.tx_txt('ACQ:TRIG:STAT?')
                if rp_s.rx_txt() == 'TD' or time.time() > trigger_timeout:
                    break
            
            # Adquire dados do canal
            data = ler_canal(canal)
            
            # Calcula FFT com RBW atual
            freq, fft_db = calcular_fft(data, RBW)
            
            # Atualiza gráfico
            line.set_data(freq/1e6, fft_db)
            fig.canvas.flush_events()
            next_acquisition += intervalo_segundos
        
        # Verifica se usuário quer alterar atenuação
        if plt.waitforbuttonpress(0.05):
            cmd = input("\nDigite 'att X' para alterar atenuação: ").strip().lower()
            if cmd.startswith('att'):
                try:
                    nova_attenuacao = int(cmd.split()[1])
                    set_attenuation(canal, nova_attenuacao)
                except:
                    print("Formato inválido. Use 'att X' (ex: 'att 20')")
        
        plt.pause(0.05)

except KeyboardInterrupt:
    print("\nAquisição interrompida pelo usuário")
finally:
    rp_s.tx_txt('ACQ:STOP')
    rp_s.close()
    plt.ioff()
    plt.show()
#!/usr/bin/python3
import time
import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

IP = '10.42.0.236'
rp_s = scpi.scpi(IP)

# Parâmetros
tempo_total_segundos = 10
intervalo_segundos = 1
sample_rate = 125e6
ts = 1 / sample_rate

# Configuração inicial do RBW e atenuação
RBW = 100e3  # 100 kHz de RBW inicial
MIN_RBW = 1e3  # 1 kHz - mínimo RBW
MAX_RBW = 1e6  # 1 MHz - máximo RBW

# Configuração de atenuação para cada canal
MIN_ATT = 0
MAX_ATT = 20
atenuacao = [0, 0, 0, 0]  # Atenuação para cada canal [CH1, CH2, CH3, CH4]

# Configuração inicial
rp_s.tx_txt('ACQ:RST')
rp_s.tx_txt('ACQ:DEC 1')
rp_s.tx_txt('ACQ:TRIG:LEV 0')
rp_s.tx_txt('ACQ:TRIG:DLY 0')

# Configuração dos subplots
plt.ion()
fig, axs = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle(f'Spectrum Analyzer - 4 Canais\nRBW: {RBW/1e3:.1f} kHz | Atenuação: {atenuacao}', fontsize=16)
colors = ['r', 'g', 'b', 'm']
lines = []
frequencias = None

# Inicializa gráficos para cada canal
for i in range(4):
    row, col = divmod(i, 2)
    line, = axs[row, col].plot([], [], colors[i], label=f'CH{i+1}')
    lines.append(line)
    axs[row, col].set_xlim(0, sample_rate/2/1e6)  # MHz
    axs[row, col].set_xticks(np.arange(0, sample_rate/2/1e6, 5))
    axs[row, col].set_ylim(-80, 80)
    axs[row, col].set_xlabel('Frequência (MHz)')
    axs[row, col].set_ylabel('Amplitude (dB)')
    axs[row, col].grid(True)
    axs[row, col].legend()

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
        atenuacao[channel-1] = att_db
        fig.suptitle(f'Spectrum Analyzer - 4 Canais\nRBW: {RBW/1e3:.1f} kHz | Atenuação: {atenuacao}', fontsize=16)
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

def atualizar_rbw(nova_rbw):
    """Atualiza o valor de RBW"""
    global RBW
    RBW = max(MIN_RBW, min(nova_rbw, MAX_RBW))
    fig.suptitle(f'Spectrum Analyzer - 4 Canais\nRBW: {RBW/1e3:.1f} kHz | Atenuação: {atenuacao}', fontsize=16)
    print(f"\nRBW alterada para: {RBW/1e3:.1f} kHz")

start_time = time.time()
next_acquisition = start_time

try:
    print("Iniciando aquisição nos 4 canais...")
    print("Pressione Ctrl+C para parar")
    print("Comandos disponíveis durante a execução:")
    print(" - 'rbw X' para alterar RBW (ex: 'rbw 10' para 10kHz)")
    print(" - 'att C X' para alterar atenuação (ex: 'att 1 20' para 20dB no CH1)")
    
    # APLICA A ATENUAÇÃO INICIAL PARA TODOS OS CANAIS
    for ch in range(4):
        set_attenuation(ch+1, atenuacao[ch])
    
    while time.time() - start_time < tempo_total_segundos:
        if time.time() >= next_acquisition:
            print(f"\nAquisição em {datetime.now().strftime('%H:%M:%S')} - RBW: {RBW/1e3:.1f} kHz - Atenuação: {atenuacao}")
            
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
                data = ler_canal(ch+1)
                
                freq, fft_db = calcular_fft(data, RBW)
                if frequencias is None:
                    frequencias = freq
                
                lines[ch].set_data(freq/1e6, fft_db)  # Converte para MHz
            
            fig.canvas.flush_events()
            next_acquisition += intervalo_segundos
        
        # Verifica se usuário quer alterar configurações
        if plt.waitforbuttonpress(0.05):
            cmd = input("\nDigite comando (rbw X / att C X): ").strip().lower()
            try:
                if cmd.startswith('rbw'):
                    nova_rbw = float(cmd.split()[1]) * 1e3
                    atualizar_rbw(nova_rbw)
                elif cmd.startswith('att'):
                    parts = cmd.split()
                    canal = int(parts[1])
                    att = int(parts[2])
                    if 1 <= canal <= 4:
                        set_attenuation(canal, att)
                    else:
                        print("Canal inválido. Use 1-4.")
                else:
                    print("Comando desconhecido")
            except:
                print("Formato inválido. Use:")
                print(" - 'rbw X' para alterar RBW (ex: 'rbw 10')")
                print(" - 'att C X' para alterar atenuação (ex: 'att 1 20')")
        
        plt.pause(0.05)

except KeyboardInterrupt:
    print("\nAquisição interrompida pelo usuário")
finally:
    rp_s.tx_txt('ACQ:STOP')
    rp_s.close()
    plt.ioff()
    plt.show()
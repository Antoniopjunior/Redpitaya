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

# Configuração inicial do RBW e Atenuação
RBW = 100e3  # 100 kHz de RBW inicial
MIN_RBW = 1e3  # 1 kHz - Mínimo RBW
MAX_RBW = 1e6  # 1 MHz - Máximo RBW

# Opções de atenuação (em dB)
ATENUACAO_OPCOES = [0, 20]  # 0dB ou 20dB
atenuacao = [0, 0, 0, 0]  # Atenuação inicial para cada canal [CH1, CH2, CH3, CH4]

# Configuração inicial
rp_s.__configure__()

# Configuração dos subplots
plt.ion()
fig, axs = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle(f'Spectrum Analyzer - 4 Canais\nRBW: {RBW/1e3:.1f} kHz | Atenuação: {atenuacao}', fontsize=16)
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
    n_rbw = min(n_rbw, n)  # não pode ser maior que o buffer
    n_rbw = max(n_rbw, 2)  # pelo menos 2 pontos
    
    # Recorta o sinal para o novo tamanho
    sinal_recortado = sinal[:n_rbw] 
    
    window = np.hanning(n_rbw)
    fft_result = np.fft.fft(sinal_recortado * window)
    fft_freq = np.fft.fftfreq(n_rbw, d=ts)[:n_rbw//2]
    fft_db = 20 * np.log10(np.abs(fft_result[:n_rbw//2]) + 1e-10)
    
    return fft_freq, fft_db

def set_attenuation(channel, att_db):
    """Configura a atenuação para um canal específico"""
    if att_db in ATENUACAO_OPCOES:
        # Na Red Pitaya, LV = 0dB (baixa tensão), HV = 20dB (alta tensão)
        rp_s.tx_txt(f'ACQ:SOUR{channel}:GAIN {"LV" if att_db == 0 else "HV"}')
        atenuacao[channel-1] = att_db
        return True
    else:
        print(f"Atenuação {att_db}dB não suportada. Use {ATENUACAO_OPCOES}")
        return False

def atualizar_rbw(nova_rbw):
    """Atualiza o valor de RBW"""
    global RBW
    RBW = max(MIN_RBW, min(nova_rbw, MAX_RBW))
    fig.suptitle(f'Spectrum Analyzer - 4 Canais\nRBW: {RBW/1e3:.1f} kHz | Atenuação: {atenuacao}', fontsize=16)
    print(f"\nRBW alterada para: {RBW/1e3:.1f} kHz")

start_time = time.time()
next_acquisition = start_time

try:
    print("Iniciando aquisição... Pressione Ctrl+C para parar")
    print("Comandos disponíveis durante a execução:")
    print(" - 'rbw X' para alterar RBW (ex: 'rbw 10' para 10kHz)")
    print(f" - 'att C X' para alterar atenuação (ex: 'att 1 20' para 20dB no CH1)")
    
    # Configura atenuação inicial
    for ch in range(4):
        set_attenuation(ch+1, atenuacao[ch])
    
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
            
            fig.suptitle(f'Spectrum Analyzer - 4 Canais\nRBW: {RBW/1e3:.1f} kHz | Atenuação: {atenuacao}', fontsize=16)
            fig.canvas.flush_events()
            next_acquisition += intervalo_segundos
        
        # Verifica comandos do usuário
        if plt.waitforbuttonpress(0.05):
            cmd = input("\nDigite comando (rbw/att): ").strip().lower()
            try:
                if cmd.startswith('rbw'):
                    nova_rbw = float(cmd.split()[1]) * 1e3
                    atualizar_rbw(nova_rbw)
                elif cmd.startswith('att'):
                    parts = cmd.split()
                    canal = int(parts[1])
                    att = int(parts[2])
                    if 1 <= canal <= 4 and set_attenuation(canal, att):
                        print(f"Atenuação do CH{canal} alterada para {att}dB")
                    else:
                        print("Canal inválido (1-4) ou atenuação não suportada")
                else:
                    print("Comando desconhecido")
            except:
                print("Formato inválido. Use 'rbw X' ou 'att C X'")
        
        plt.pause(0.01)

except KeyboardInterrupt:
    print("\nAquisição interrompida pelo usuário")
finally:
    rp_s.tx_txt('ACQ:STOP')
    rp_s.close()
    plt.ioff()
    plt.show()
#!/usr/bin/python3
import time
import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

IP = '10.42.0.25'
rp_s = scpi.scpi(IP)

# Parâmetros
tempo_total_segundos = 300  # Tempo total de execução
tempo_atualizacao = 0.2    # Intervalo entre atualizações (segundos)
sample_rate = 125e6        # Taxa de amostragem
ts = 1 / sample_rate       # Período de amostragem

# Configuração RBW
RBW = 100e3  # Resolution Bandwidth inicial (100 kHz)
MIN_RBW = 1e3  # 1 kHz
MAX_RBW = 1e6  # 1 MHz

# Configuração de Atenuação
ATENUACAO_OPCOES = [0, 20]  # 0dB ou 20dB
atenuacao = [0, 0, 0, 0]  # Atenuação inicial para cada canal [CH1, CH2, CH3, CH4]

# Variáveis para controle das escalas globais do osciloscópio
amplitudes_maximas = []
amplitudes_minimas = []
global_max = float('-inf')
global_min = float('inf')

# Configuração inicial
rp_s.tx_txt('ACQ:RST')
rp_s.tx_txt('ACQ:DEC 1')
rp_s.tx_txt('ACQ:TRIG:LEV 0')
rp_s.tx_txt('ACQ:TRIG:DLY 0')

# Configuração da interface
plt.ion()
fig = plt.figure(figsize=(16, 12))
fig.suptitle(f'Osciloscópio + Spectrum Analyzer - RBW: {RBW/1e3:.1f} kHz | Atenuação: {atenuacao}', fontsize=16)

# Cria subplots para cada canal (4 linhas, 2 colunas)
axs_osc = []  # Para os gráficos do osciloscópio
axs_spec = [] # Para os gráficos do spectrum analyzer
lines_osc = []
lines_spec = []

for i in range(4):
    # Gráfico do osciloscópio (esquerda)
    ax_osc = plt.subplot(4, 2, 2*i+1)
    line_osc, = ax_osc.plot([], [], 'b', label=f'CH{i+1} - Temporal')
    ax_osc.set_xlabel('Tempo (s)')
    ax_osc.set_ylabel('Tensão (V)')
    ax_osc.grid(True)
    ax_osc.legend()
    
    # Gráfico do spectrum analyzer (direita)
    ax_spec = plt.subplot(4, 2, 2*i+2)
    line_spec, = ax_spec.plot([], [], 'r', label=f'CH{i+1} - Frequência')
    ax_spec.set_xlim(0, sample_rate/2/1e6)  # MHz
    ax_spec.set_ylim(-80, 80)
    ax_spec.set_xlabel('Frequência (MHz)')
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

def ler_canal(canal):
    """Lê os dados de um canal específico"""
    rp_s.tx_txt(f'ACQ:SOUR{canal}:DATA?')
    data_str = rp_s.rx_txt().strip('{}\n\r').replace("  ", "").split(',')
    return np.array(list(map(float, data_str)))

def set_attenuation(channel, att_db):
    """Configura a atenuação para um canal específico"""
    global atenuacao
    if att_db in ATENUACAO_OPCOES:
        rp_s.tx_txt(f'ACQ:SOUR{channel}:GAIN {"LV" if att_db == 0 else "HV"}')
        atenuacao[channel-1] = att_db
        return True
    else:
        print(f"Atenuação {att_db}dB não suportada. Use {ATENUACAO_OPCOES}")
        return False

def atualizar_rbw(nova_rbw):
    """Atualiza o valor de RBW e o título do gráfico"""
    global RBW
    RBW = max(MIN_RBW, min(nova_rbw, MAX_RBW))
    fig.suptitle(f'Osciloscópio + Spectrum Analyzer - RBW: {RBW/1e3:.1f} kHz | Atenuação: {atenuacao}', fontsize=16)
    print(f"\nRBW alterada para: {RBW/1e3:.1f} kHz")

start_time = time.time()
next_acquisition = start_time

try:
    print("Iniciando aquisição... Pressione Ctrl+C para parar")
    print("Comandos disponíveis durante a execução:")
    print(" - 'rbw X' para alterar RBW (ex: 'rbw 10' para 10kHz)")
    print(" - 'att C X' para alterar atenuação (ex: 'att 1 20' para 20dB no CH1)")
    
    # Configura atenuação inicial para todos os canais
    for ch in range(4):
        set_attenuation(ch+1, atenuacao[ch])
    
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
            current_maxes = []
            current_mins = []
            
            for ch in range(4):
                data = ler_canal(ch+1)
                time_axis = np.arange(len(data)) / sample_rate
                
                # Calcula amplitudes máxima e mínima deste canal
                chan_max = np.max(data)
                chan_min = np.min(data)
                current_maxes.append(chan_max)
                current_mins.append(chan_min)
                
                # Atualiza osciloscópio
                lines_osc[ch].set_data(time_axis, data)
                
                # Atualiza spectrum analyzer com RBW atual
                freq, fft_db, _ = calcular_fft(data, RBW)
                lines_spec[ch].set_data(freq/1e6, fft_db)
                axs_spec[ch].relim()
                axs_spec[ch].autoscale_view(True, True, True)
            
            # Armazena amplitudes desta aquisição
            amplitudes_maximas.append(current_maxes)
            amplitudes_minimas.append(current_mins)
            
            # Atualiza limites globais
            current_global_max = np.max(current_maxes)
            current_global_min = np.min(current_mins)
            
            global_max = max(global_max, current_global_max)
            global_min = min(global_min, current_global_min)
            
            # Aplica margem às escalas do osciloscópio
            margin = 0.1
            y_min = global_min - margin
            y_max = global_max + margin
            
            # Define o limite de tempo baseado na duração do sinal
            x_max = time_axis[-1] if time_axis is not None else 1.0
            
            print(f"Amplitudes - Global: [{global_min:.3f}V, {global_max:.3f}V]")
            
            # Ajusta escalas dos gráficos do osciloscópio
            for ch in range(4):
                axs_osc[ch].set_xlim(0, x_max)
                axs_osc[ch].set_ylim(y_min, y_max)
                axs_osc[ch].relim()
                axs_osc[ch].autoscale_view(True, True, True)
            
            fig.suptitle(f'Osciloscópio + Spectrum Analyzer - RBW: {RBW/1e3:.1f} kHz | Atenuação: {atenuacao}', fontsize=16)
            fig.canvas.flush_events()
            next_acquisition = time.time() + tempo_atualizacao
        
        # Verifica se há comando do usuário
        if plt.waitforbuttonpress(0.01):
            cmd = input("\nComando (rbw X / att C X): ").strip()
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
                        fig.suptitle(f'Osciloscópio + Spectrum Analyzer - RBW: {RBW/1e3:.1f} kHz | Atenuação: {atenuacao}', fontsize=16)
                    else:
                        print("Canal inválido (1-4) ou atenuação não suportada")
                else:
                    print("Comando desconhecido. Use 'rbw X' ou 'att C X'")
            except:
                print("Formato inválido. Use:")
                print(" - 'rbw X' para alterar RBW (ex: 'rbw 10')")
                print(" - 'att C X' para alterar atenuação (ex: 'att 1 20')")

except KeyboardInterrupt:
    print("\nAquisição interrompida pelo usuário")
    
    # Mostra estatísticas finais
    print(f"\n--- Estatísticas Finais ---")
    print(f"Total de aquisições: {len(amplitudes_maximas)}")
    print(f"Amplitude mínima global: {global_min:.3f}V")
    print(f"Amplitude máxima global: {global_max:.3f}V")
    
finally:
    rp_s.tx_txt('ACQ:STOP')
    rp_s.close()
    plt.ioff()
    plt.show()
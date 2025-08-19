#!/usr/bin/python3
import time
import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

IP = '10.42.0.25' # SO Windows: 169.254.56.223 | SO Linux Ubuntu: 10.4.0.25
rp_s = scpi.scpi(IP)

# Parâmetros
tempo_total_segundos = 30  # Tempo total de execução
tempo_atualizacao = 0.2    # Intervalo entre atualizações (segundos)
buffer_size = 16384        # Tamanho do buffer de aquisição
sample_rate = 125e6        # Taxa de amostragem
ts = 1 / sample_rate       # Período de amostragem
canal = 1

# Configuração RBW
RBW = 100e3  # Resolution Bandwidth inicial (100 kHz)
MIN_RBW = 1e3  # 1 kHz
MAX_RBW = 1e6  # 1 MHz

# Opções de atenuação (em dB)
atenuacao = 0 # Digite a atenuação desejada
ATT_MAX = 20 # Atenuação máxima permitida pela red pitaya
ATT_MIN = 0 # Atenuação mínima permitida pela red pitaya

# Configuração inicial
rp_s.__configure__()

# Configuração da interface
plt.ion()
fig = plt.figure(figsize=(16, 12))
fig.suptitle(f'Osciloscópio e Spectrum Analyzer - Canal {canal}\nRBW: {RBW/1e3:.1f} kHz | Atenuação: {atenuacao}dB', fontsize=16)

# Criação dos subplots para o canal único 

#osciloscópio
ax_osc = plt.subplot(2, 1, 1)
line_osc, = ax_osc.plot([], [], 'b', label = f'CH{canal} - Temporal')
ax_osc.set_xlim(0, buffer_size)
ax_osc.set_ylim(-1.1, 1.1)
ax_osc.set_xlabel('Tensão (V)')
ax_osc.set_ylabel('Amostras')
ax_osc.grid(True)
ax_osc.legend()

#spectrum analyzer
ax_spec = plt.subplot(2, 1, 2)
line_spec, = ax_spec.plot([], [], 'r', label=f'CH{canal} - Frequência')
ax_spec.set_xlim(0, sample_rate/2/1e6)
ax_spec.set_ylim(-80, 10)
ax_spec.set_ylabel('Amplitude (dB)')
ax_spec.set_xlabel('Frequência (MHz)')
ax_spec.grid(True)
ax_spec.legend()

plt.tight_layout()

def calcular_fft(sinal, rbw):
    #Calcular a FFT com RBW específica
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
    # Atualiza o valor de RBW e o titulo do gráfico
    global RBW
    RBW = max(MIN_RBW, min(nova_rbw, MAX_RBW))
    fig.suptitle(f'Osciloscópio e Spectrum Analyzer - Canal {canal}\nRBW: {RBW/1e3:.1f} kHz | Atenuação: {atenuacao}dB', fontsize=16)
    print(f"\nRBW alterada para: {RBW/1e3:.1f} kHz")

def set_attenuation(canal, att_db):
    # Configura a atenuação para o canal
    global atenuacao
    if ATT_MIN <= att_db <= ATT_MAX:
        rp_s.tx_txt(f'ACQ:SOUR{canal}:GAIN {"LV" if att_db == 0 else "HV"}')
        atenuacao = att_db
        fig.suptitle(f'Osciloscópio e Spectrum Analyzer - Canal {canal}\nRBW: {RBW/1e3:.1f} kHz | Atenuação: {atenuacao}dB', fontsize=16)
        print(f"Atenuação alerada para: {att_db}dB")
        return True
    else:
        print(f"Atenuação {att_db}dB não suportada. Use valores entre {ATT_MIN} e {ATT_MAX} dB")
        return False

start_time = time.time()
next_acquisition = start_time

try:
    print("Iniciando aquisição... Pressione Crtl+C para parar")
    print("Digite 'rbw X' para alterar a RBW para X kHz (ex: 'att 20')")
    print("Digite 'att X' para alterar a atenuação para X dB (ex: 'att 20')")
    
    set_attenuation(canal, atenuacao)
    
    while time.time() - start_time < tempo_total_segundos:
        if time.time() >= next_acquisition:
            
            print(f"\nAquisição em {datetime.now().strftime('%H:%M:%S')}")
            
            #Configura trigger no canal escolhido
            rp_s.tx_txt(f'ACQ:TRIG CH{canal}_PE')
            rp_s.tx_txt('ACQ:START')
            
            #Espera trigger
            trigger_timeout = time.time() + 0.5
            while True:
                rp_s.tx_txt('ACQ:TRIG:STAT?')
                if rp_s.rx_txt() == 'TD' or time.time() > trigger_timeout:
                    break
                
            # Leitura dos dados do canal escolhido
            data = rp_s.ler_canal(canal)
            time_axis = np.arange(len(data))
            
            #Atualiza o osciloscópio
            line_osc.set_data(time_axis, data)
            ax_osc.relim()
            ax_osc.autoscale_view(True, True, True)
            
            fig.canvas.flush_events()
            next_acquisition = time.time() + tempo_atualizacao
            
        # Verifica se há comando do usuário
        if plt.waitforbuttonpress(0.01):
            cmd = input("\nComando (rbw X / att X): ").strip().lower()
            if cmd.startswith('rbw'):
                try:
                    nova_rbw = float(cmd.split()[1]) * 1e3
                    atualizar_rbw(nova_rbw)
                except:
                    print("Formato inválido. Use 'rbw X' (ex: 'rbw 10')")
            elif cmd.startswith('att'):
                try:
                    nova_attenuacao = float(cmd.split()[1])
                    set_attenuation(nova_attenuacao)
                except:
                    print("Formato inválido. Use 'att X' (ex: 'att 20')")

except KeyboardInterrupt:
    print("\nAquisição interrompida pelo usuário")
finally:
    rp_s.tx_txt('ACQ:STOP')
    rp_s.close()
    plt.ioff()
    plt.show()
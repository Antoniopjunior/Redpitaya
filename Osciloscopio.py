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
buffer_size = 16384        # Tamanho do buffer de aquisição
sample_rate = 125e6        # Taxa de amostragem

# Configuração inicial
rp_s.tx_txt('ACQ:RST')
rp_s.tx_txt('ACQ:DEC 1')
rp_s.tx_txt('ACQ:TRIG:LEV 0')
rp_s.tx_txt('ACQ:TRIG:DLY 0')

# Configuração dos subplots
plt.ion()
fig, axs = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle('Osciloscópio - Red Pitaya', fontsize=16)
colors = ['r', 'b', 'g', 'm']
lines = []
time_axis = None

# Variáveis para controle das escalas globais
amplitudes_maximas = []  # Armazenará as amplitudes máximas de cada aquisição
amplitudes_minimas = []  # Armazenará as amplitudes mínimas de cada aquisição
global_max = float('-inf')
global_min = float('inf')

# Inicializa gráficos
for i in range(4):
    row, col = divmod(i, 2)
    line, = axs[row, col].plot([], [], colors[i], label=f'CH{i+1}')
    lines.append(line)
    axs[row, col].set_xlabel('Tempo (s)')
    axs[row, col].set_ylabel('Tensão (V)')
    axs[row, col].grid(True)
    axs[row, col].legend()

plt.tight_layout()

def ler_canal(canal):
    """Lê os dados de um canal específico"""
    rp_s.tx_txt(f'ACQ:SOUR{canal}:DATA?')
    data_str = rp_s.rx_txt().strip('{}\n\r').replace("  ", "").split(',')
    return np.array(list(map(float, data_str)))

start_time = time.time()
next_acquisition = start_time

try:
    while time.time() - start_time < tempo_total_segundos:
        if time.time() >= next_acquisition:
            
            print(f"\nAquisição em {datetime.now().strftime('%H:%M:%S')}")
            # Configura trigger no canal 1
            rp_s.tx_txt('ACQ:TRIG CH1_PE')
            
            # Inicia aquisição
            rp_s.tx_txt('ACQ:START')
            
            # Espera trigger
            trigger_timeout = time.time() + 0.5
            while True:
                rp_s.tx_txt('ACQ:TRIG:STAT?')
                if rp_s.rx_txt() == 'TD' or time.time() > trigger_timeout:
                    break
            
            # Adquire dados dos quatro canais
            current_maxes = []
            current_mins = []
            
            for ch in range(4):
                data = ler_canal(ch+1)
                
                # Converte amostras para tempo
                if time_axis is None:
                    time_axis = np.arange(len(data)) / sample_rate
                
                # Calcula amplitudes máxima e mínima deste canal
                chan_max = np.max(data)
                chan_min = np.min(data)
                current_maxes.append(chan_max)
                current_mins.append(chan_min)
                
                # Atualiza linha do gráfico
                lines[ch].set_data(time_axis, data)
            
            # Armazena amplitudes desta aquisição
            amplitudes_maximas.append(current_maxes)
            amplitudes_minimas.append(current_mins)
            
            # Atualiza limites globais
            current_global_max = np.max(current_maxes)
            current_global_min = np.min(current_mins)
            
            global_max = max(global_max, current_global_max)
            global_min = min(global_min, current_global_min)
            
            # Aplica margem às escalas (exatamente como no seu código)
            margin = 0.1
            y_min = global_min - margin
            y_max = global_max + margin
            
            # Define o limite de tempo baseado na duração do sinal
            x_max = time_axis[-1] if time_axis is not None else 1.0
            
            print(f"Amplitudes - Global: [{global_min:.3f}V, {global_max:.3f}V]")
            print(f"Escala Y ajustada para: [{y_min:.3f}V, {y_max:.3f}V]")
            
            # Ajusta escalas de todos os gráficos
            for i in range(4):
                row, col = divmod(i, 2)
                axs[row, col].set_xlim(0, x_max)
                axs[row, col].set_ylim(y_min, y_max)
                
                # Atualiza a visualização
                axs[row, col].relim()
                axs[row, col].autoscale_view(True, True, True)
            
            fig.canvas.flush_events()
            next_acquisition = time.time() + tempo_atualizacao
            
        plt.pause(0.01)

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
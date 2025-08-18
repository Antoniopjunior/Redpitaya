import time
import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

IP = '10.42.0.25'
rp_s = scpi.scpi(IP)

#Parâmetros 
tempo_total_segundos = 30
tempo_atualizacao = 0.2
buffer_size = 16384
canal = 1 #digite aqui o número do canal a ser analisado 

#Configuração inicial
rp_s.__configure__()

#Configuração do gráfico
plt.ion()
fig, ax = plt.subplots(figsize=(15, 7))
fig.suptitle(f'Osciloscópio - Canal {canal}', fontsize=16)

#Configuração da linha do gráfico
line, = ax.plot([], [], 'b', label = f'CH{canal}')
ax.set_xlim(0, buffer_size)
ax.set_ylim(-1.1, 1.1)
ax.set_xlabel('Amostras')
ax.set_ylabel('Tensão (V)')
ax.grid(True)
ax.legend()

plt.tight_layout()

start_time = time.time()
next_acquisition = start_time

try: 
    while time.time() - start_time < tempo_total_segundos:
        if time.time() >= next_acquisition:
            
            print(f"\n Aquisição em {datetime.now().strftime('%H:%M:%S')}")
            
            #Configuração do trigger no canal escolhido 
            rp_s.tx_txt(f'ACQ:TRIG CH{canal}_PE')
            
            #Inciando a aquisição
            rp_s.tx_txt('ACQ:START')
            
            # Esperando pelo trigger
            trigger_timeout = time.time() + 0.5
            while True:
                rp_s.tx_txt('ACQ:TRIG:STAT?')
                if rp_s.rx_txt() == 'TD' or time.time() > trigger_timeout:
                    break
            
            #Adquirindo os dados
            data = rp_s.ler_canal(canal)
            time_axis = np.arange(len(data))
            
            #Atualizando o gráfico
            line.set_data(time_axis, data)
            ax.relim()
            ax.autoscale_view(True, True, True)
            fig.canvas.flush_events()
            
            next_acquisition = time.time() + tempo_atualizacao
            
        plt.pause(0.01)
        
except KeyboardInterrupt:
    print("\nAquisição interrompida pelo usuário")
finally:
    rp_s.tx_txt('ACQ:STOP')
    rp_s.close()
    plt.ioff()
    plt.show()

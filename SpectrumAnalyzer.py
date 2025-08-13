import numpy as np
import matplotlib.pyplot as plt
import redpitaya_scpi as scpi

#definição das constantes
FS = 125e6
BUFFER_SIZE = 16384
DECIMATION = 8

#Conexão com a redpitaya
IP = '169.254.56.223'
rp_s = scpi.scpi(IP)

#Padronização para identificação dos canais
colors = ['b', 'g', 'r', 'm']
channels = [1, 2, 3, 4]

#Configuração inicial
rp_s.spectrumAnalyzerConf(DECIMATION, 0) #configurando com a decimação e o nível do trigger

#Configuração 
plt.ion()
fig, ax = plt.subplots(figsize = (10, 6))
lines = []


for i, channel in enumerate(channels):
    line, = ax.plot([], [], colors[i], label=f"Canal {channel}")
    lines.append(line)

ax.set_xlim(0, (FS/DECIMATION)/2/1e6)
ax.set_ylim(-100, 0)
ax.set_xlabel("Frequência (MHz)")
ax.set_ylabel("Magnitude (dB)")
ax.set_title("Spectrum Analyzer - 4 inputs")
ax.legend()
ax.grid(True)

try:
    while True:
        for i, channel in enumerate(channels):
            data = rp_s.ler_canal(channel)
            
            # Aplica uma janela (Hanning) para reduzir vazamento espectral
            window = np.hanging(len(data))
            data_windowed = data * window
            
            # Calcula a FFT
            fft_data = np.fft.fft(data_windowed)
            fft_mag = 20 * np.log10(np.abs(fft_data) + 1e-10)
            
            # Obtém as frequências positivas (metade do espectro)
            freq = np.fft.fftfreq(len(data), d=1/(FS/DECIMATION))
            positive_freq = freq[:len(freq)//2]
            positive_fft = fft_mag[:len(fft_mag)//2]
            
            #Atualização dos gráficos
            lines[i].set_xdata(positive_freq / 1e6)
            lines[i].set_ydata(positive_fft)
            
        ax.relim()
        ax.autoscale_view()
        fig.canvas.flush_events()
        plt.pause(0.1) #taxa de atualização 
except:
    print("Parando o Spectrum Analyzer")
    rp_s.tx_txt("ACQ:STOP")
    rp_s.close()
    plt.close()
    
#versão geral usando os quatro inputs, verificar se ele pode funcionar junto com o osciloscópio depois
# realizar teste
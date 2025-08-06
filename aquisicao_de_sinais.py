#!/usr/bin/python3
import time
import sys
import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from datetime import datetime

IP = '169.254.56.223'
rp_s = scpi.scpi(IP)

# Parâmetros de aquisição
tempo_total_segundos = 5  # tempo total de aquisição
intervalo_segundos = 1     # intervalo entre aquisições

# Diretório de saída
output_dir = "curvas_redpitaya"
os.makedirs(output_dir, exist_ok=True)

# Configuração inicial
rp_s.tx_txt('ACQ:RST')
rp_s.tx_txt('ACQ:DEC 1')
rp_s.tx_txt('ACQ:DATA:FORMAT ASCII')
rp_s.tx_txt('ACQ:DATA:UNITS VOLTS')
rp_s.tx_txt('ACQ:TRIG:LEV 0')
rp_s.tx_txt('ACQ:TRIG:DLY 0')

# Começa o temporizador
start_time = time.time()

while time.time() - start_time < tempo_total_segundos:
    rp_s.tx_txt('ACQ:START')
    rp_s.tx_txt('ACQ:TRIG CH2_PE')

    # Espera o trigger
    while True:
        rp_s.tx_txt('ACQ:TRIG:STAT?')
        if rp_s.rx_txt() == 'TD':
            break

    # Espera o buffer encher
    while True:
        rp_s.tx_txt('ACQ:TRIG:FILL?')
        if rp_s.rx_txt() == '1':
            break

    # Função para ler dados de canal
    def ler_canal(canal):
        rp_s.tx_txt(f'ACQ:SOUR{canal}:DATA?')
        raw = rp_s.rx_txt()
        raw = raw.strip('{}\n\r').replace("  ", "").split(',')
        return np.array(list(map(float, raw)))

    # Leitura dos canais
    buff1 = ler_canal(1)
    buff2 = ler_canal(2)
    buff3 = ler_canal(3)
    buff4 = ler_canal(4)

    # Eixo de tempo
    sample_rate = 125e6  # Red Pitaya ADC = 125 MHz
    ts = 1 / sample_rate
    tempo = np.arange(len(buff1)) * ts

    # Timestamp para nome dos arquivos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Salva os dados em CSV
    filename = os.path.join(output_dir, f"curvas_{timestamp}.csv")
    np.savetxt(
        filename,
        np.column_stack((tempo, buff1, buff2, buff3, buff4)),
        delimiter=',',
        header='tempo,buff1,buff2,buff3,buff4',
        comments=''
    )
    print(f"[{timestamp}] Curvas salvas em {filename}")

    # Espera próximo ciclo
    time.sleep(intervalo_segundos)

print("Aquisição finalizada.")


#######################################################################################

caminho_csv = r"C:\Users\antonio.pjunior\Documents\Python\hantek_usb_control\Dados\F35_12.csv"

try:
    df = pd.read_csv(caminho_csv, skipinitialspace=True, usecols=[0,1,2], header=None)
except Exception as e:
    print("Erro ao ler o arquivo CSV:", e)
    exit()

df.columns = ["Time [s]", "CH1 [V]", "CH2 [V]"]

# Garante que as colunas são numéricas
for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df = df.dropna(subset=df.columns)

if len(df) < 10:
    print("Dados insuficientes para plotar.")
    exit()

plt.figure(figsize=(10, 4))
plt.plot(df["Time [s]"], df["CH1 [V]"], label="Canal 1 (CH1)", linewidth=1)
plt.plot(df["Time [s]"], df["CH2 [V]"], label="Canal 2 (CH2)", linewidth=1)
plt.xlabel("Tempo (s)")
plt.ylabel("Tensão (V)")
plt.title("Forma de onda - CH1 e CH2")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
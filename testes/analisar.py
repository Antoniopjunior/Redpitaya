import pandas as pd
import matplotlib.pyplot as plt

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

import redpitaya_scpi as scpi
import time

# Configuração inicial
rp = scpi.scpi('10.42.0.25')  # IP da sua Red Pitaya

def read_single_value(canal):
    # Configuração da aquisição
    rp.tx_txt('ACQ:DEC 1')          
    rp.tx_txt(f'ACQ:SOUR{canal}:GAIN HV')  
    rp.tx_txt('ACQ:TRIG:LEV 0')     
    rp.tx_txt('ACQ:START')          
    
    # Pequena pausa para estabilização
    time.sleep(0.01)
    
    
    rp.tx_txt(f'ACQ:SOUR{canal}:DATA:OLD:N? 1')
    
    # Recebe e processa o dado
    data = rp.rx_txt()
    try:
        # Remove caracteres especiais e converte para float
        value = float(data.strip('{}\n\r').split(',')[-1])  # Pega a última amostra
        return value
    except ValueError:
        print(f"Erro na conversão do valor: {data}")
        return None

# Loop de leitura contínua
print("Lendo valores instantâneos. Ctrl+C para parar.")
try:
    while True:
        sum_voltage = read_single_value(4)
        x_voltage = read_single_value(3)
        y_voltage = read_single_value(2)
        
       
        if sum_voltage is not None and x_voltage is not None and y_voltage is not None:
            print(f"SUM: {sum_voltage:.3f} V")
            print(f'X: {x_voltage:.3f} V')
            print(f'Y: {y_voltage:.3f} V')
            print("-" * 20)  
        
        time.sleep(1)  

except KeyboardInterrupt:
    print("\nLeitura interrompida pelo usuário")

# Limpeza final
rp.tx_txt('ACQ:STOP')
print("Aquisição finalizada.")
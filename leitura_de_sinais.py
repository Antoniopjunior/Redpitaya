import numpy as np
import time
import sys
from redpitaya_scpi import scpi
 
#configurando a RedPitaya
IP = '169.254.56.223'
rp = scpi.scpi(IP)
 
#Resetando as informações
rp.tx_txt("ACQ:RST") #o comando tx_txt é usado para escrever comando scpi para a RedPitaya e o ACQ:RST limpa os buffers de aquisição
rp.tx_txt("ACQ:START")
rp.tx_txt("ACQ:DATA:FORMAT ASCII") #formatando os dados em texto
rp.tx_txt("ACQ:DEC 1") #definindo a decimação
rp.tx_txt("ACQ:TRIG:LEV 0.1") #definindo o nível do trigger, nesse caso 0.1V
rp.tx_txt("ACQ:TRIG CH1_PE") #trigger na borda positiva do Canal 1 (acusa toda vez que o sinal sobe o nível definido acima por TRIG:LEV)
 
#Iniciando a aquisição

 
while True:
    rp.tx_txt("ACQ:TRIG:STAT?") #pergunta para a RedPitaya se o trigger foi ativado
    if rp.rx_txt() == "TD": #verfica a resposta da RedPitaya (TD - Trigger Detected)
        break
    time.sleep(0.01)
 
#Leitura dos dados do canala
rp.tx_txt("ACQ:SOUR:CH1:DATA?")
raw = rp.rx_txt()
 
#Convertendo os dados para um array numpy
raw_str = raw.split('{}\n\r')
data_ch1 = np.array(list(map(float, raw_str('{}\n\r').split(','))))
 
#Exibindo os dados
print("Amostras do Canal 1")
print(data_ch1[:10])
 
# Redpitaya

Este projeto implementa um osciloscópio e analisador de espectro utilizando a placa Redítaya, controlando-a via interface SCPI e exibindo os resultados em tempo real atraés de gráficos em "tempo real".

## 📋 Funcionalidades 
* Osciloscópio em "tempo real": Visualização de sinais no domínio do tempo

* Analisador de espectro: Transformada de Fourier (FFT) com ajuste de RBW

* Controle de atenuação: Ajuste de ganho (LV/HV) para diferentes faixas de tensão

* Interface interativa: Controle dos parâmetros durante a execução

* Aquisição por trigger: Captura de sinais com trigger configurável

## 🛠️ Pré-requisitos
* Placa Redpitaya
* Python 3.x
* Bibliotecas Python:
    * redpitaya_scpi
    * matplotlib
    * numpy
    * datetime

## 🔧 Instalação 

1. Clone o repositório:

git clone https://github.com/Antoniopjunior/Redpitaya.git
cd Redpitaya

2. Instale as dependências:

pip install matplotlib numpy

3. Certifique-se de ter a biblioteca redpitaya_scpi intalada

## 📡 Configuração de Rede
Antes de executar, configure o IP da Redpitaya no código

IPs comuns:

* Windows: 169.254.56.223
* Linux Ubuntu: 10.42.0.25


### Parâmetros ajustáveis no código:

* Tempoo total de execução (em segundos)
* Intervalo entre as atualizações (em segundos)
* Tamanho do buffer de aquisição
* Canal
* RBW (limite definido, verifique no código)
* Atenuação (limite definido, verifique no código)

## 📊 Características Técnicas
* Taxa de amostragem: 125 MSa/s
* Resolução ADC: 14 bits
* Faixa de tensão:
    * Modo LV (baixa tensão): ±1V
    * Modo HV (alta tensão): ±20V
* RBW ajustável: 1 kHz a 1 MHz
* Atenuação ajustável: 0 a 20 dB
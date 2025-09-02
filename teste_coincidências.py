import numpy as np
import matplotlib.pyplot as plt
import time
import sys
import os

# Adicionar o path para a biblioteca SCPI personalizada
sys.path.append('/path/to/Redpitaya')  # Ajuste o path conforme necessário

# Importar a biblioteca SCPI personalizada
from redpitaya_scpi import scpi

class FrequencyCoincidenceAnalyzer:
    def __init__(self, ip_address='192.168.1.100', port=5000):
        """
        Inicializa o analisador de coincidências para Red Pitaya
        usando a biblioteca SCPI personalizada
        """
        self.ip_address = ip_address
        self.port = port
        
        # Conectar com a Red Pitaya
        try:
            self.rp = scpi(ip_address, port=port)
            print(f"Conectado à Red Pitaya em {ip_address}:{port}")
        except Exception as e:
            print(f"Erro ao conectar com Red Pitaya: {e}")
            sys.exit(1)
        
        # Configurações iniciais
        self.sample_rate = 125e6  # 125 MHz para Red Pitaya
        self.buffer_size = 16384  # Tamanho do buffer
        self.time_window = 5e-9   # 5 ns de janela temporal
        
    def setup_acquisition(self, decimation=8, trigger_level=0.1):
        """
        Configura a aquisição de dados usando comandos SCPI
        """
        try:
            # Configurar decimation
            self.rp.tx_txt(f'ACQ:DEC {decimation}')
            
            # Configurar trigger para ambos os canais
            self.rp.tx_txt(f'ACQ:TRIG:LEV 0,{trigger_level}')
            self.rp.tx_txt(f'ACQ:TRIG:LEV 1,{trigger_level}')
            
            # Configurar delay do trigger
            self.rp.tx_txt('ACQ:TRIG:DLY 0')
            
            # Configurar ganho
            self.rp.tx_txt('ACQ:SOUR1:GAIN LV')
            self.rp.tx_txt('ACQ:SOUR2:GAIN LV')
            
            # Configurar formato dos dados
            self.rp.tx_txt('ACQ:DATA:FORMAT ASCII')
            self.rp.tx_txt('ACQ:DATA:UNITS VOLTS')
            
            print("Aquisição configurada com sucesso")
            
        except Exception as e:
            print(f"Erro na configuração da aquisição: {e}")
    
    def acquire_data(self):
        """
        Adquire dados de ambos os canais usando SCPI
        """
        try:
            # Reset e iniciar aquisição
            self.rp.tx_txt('ACQ:RST')
            self.rp.tx_txt('ACQ:START')
            
            # Aguardar trigger
            time.sleep(0.1)
            
            # Verificar se o trigger ocorreu
            self.rp.tx_txt('ACQ:TRIG:STAT?')
            trigger_status = self.rp.rx_txt()
            
            if 'TD' not in trigger_status:
                print("Trigger não disparado. Tentando novamente...")
                time.sleep(0.1)
                self.rp.tx_txt('ACQ:TRIG:STAT?')
                trigger_status = self.rp.rx_txt()
            
            # Parar aquisição
            self.rp.tx_txt('ACQ:STOP')
            
            # Ler dados do canal 1 usando o método da biblioteca
            data_ch1 = self.rp.ler_canal(1)
            
            # Ler dados do canal 2 usando o método da biblioteca
            data_ch2 = self.rp.ler_canal(2)
            
            # Garantir que os arrays tenham o mesmo tamanho
            min_length = min(len(data_ch1), len(data_ch2), self.buffer_size)
            data_ch1 = data_ch1[:min_length]
            data_ch2 = data_ch2[:min_length]
            
            # Criar vetor de tempo
            actual_sample_rate = self.sample_rate / 8  # decimation padrão
            t = np.arange(min_length) / actual_sample_rate
            
            return t, data_ch1, data_ch2
            
        except Exception as e:
            print(f"Erro na aquisição de dados: {e}")
            return None, None, None
    
    def find_peaks(self, data, threshold=0.05, min_distance=10):
        """
        Encontra picos nos dados - implementação manual sem scipy
        """
        try:
            peaks = []
            
            # Detecção simples de picos
            for i in range(1, len(data)-1):
                if (data[i] > data[i-1] and 
                    data[i] > data[i+1] and 
                    data[i] > threshold and
                    (len(peaks) == 0 or (i - peaks[-1]) >= min_distance)):
                    peaks.append(i)
            
            return np.array(peaks)
        except Exception as e:
            print(f"Erro na detecção de picos: {e}")
            return np.array([])
    
    def calculate_frequencies(self, t, peaks):
        """
        Calcula frequências a partir dos picos detectados
        """
        try:
            if len(peaks) < 2:
                return np.array([])
            
            # Calcular períodos entre picos
            peak_times = t[peaks]
            periods = np.diff(peak_times)
            
            # Calcular frequências (evitar divisão por zero)
            frequencies = 1.0 / periods
            frequencies = frequencies[np.isfinite(frequencies)]
            
            return frequencies
            
        except Exception as e:
            print(f"Erro no cálculo de frequências: {e}")
            return np.array([])
    
    def find_coincidences(self, t, data_ch1, data_ch2, freq_tolerance=0.01):
        """
        Analisa coincidências de frequência na janela temporal de 5 ns
        """
        try:
            # Encontrar picos em ambos os canais
            peaks_ch1 = self.find_peaks(data_ch1)
            peaks_ch2 = self.find_peaks(data_ch2)
            
            if len(peaks_ch1) < 2 or len(peaks_ch2) < 2:
                return [], [], [], peaks_ch1, peaks_ch2
            
            # Calcular frequências
            freqs_ch1 = self.calculate_frequencies(t, peaks_ch1)
            freqs_ch2 = self.calculate_frequencies(t, peaks_ch2)
            
            if len(freqs_ch1) == 0 or len(freqs_ch2) == 0:
                return [], [], [], peaks_ch1, peaks_ch2
            
            # Encontrar coincidências
            coincidences = []
            coincident_freqs = []
            time_differences = []
            
            # Para cada frequência no canal 1, verificar se há correspondência no canal 2
            for i, freq1 in enumerate(freqs_ch1):
                for j, freq2 in enumerate(freqs_ch2):
                    # Verificar se as frequências são similares dentro da tolerância
                    freq_avg = (freq1 + freq2) / 2
                    if abs(freq1 - freq2) < freq_tolerance * freq_avg:
                        # Calcular diferença temporal entre os eventos correspondentes
                        time_diff = abs(t[peaks_ch1[i+1]] - t[peaks_ch2[j+1]])
                        
                        if time_diff <= self.time_window:
                            coincidences.append((i, j))
                            coincident_freqs.append((freq1, freq2))
                            time_differences.append(time_diff)
            
            return coincidences, coincident_freqs, time_differences, peaks_ch1, peaks_ch2
            
        except Exception as e:
            print(f"Erro na análise de coincidências: {e}")
            return [], [], [], np.array([]), np.array([])
    
    def analyze_coincidence_statistics(self, coincidences, time_differences):
        """
        Analisa estatísticas das coincidências
        """
        if not coincidences:
            return {
                'total_coincidences': 0,
                'mean_time_diff': 0,
                'std_time_diff': 0,
                'min_time_diff': 0,
                'max_time_diff': 0,
                'coincidence_rate': 0
            }
        
        try:
            time_diffs = np.array(time_differences)
            
            stats = {
                'total_coincidences': len(coincidences),
                'mean_time_diff': np.mean(time_diffs),
                'std_time_diff': np.std(time_diffs),
                'min_time_diff': np.min(time_diffs),
                'max_time_diff': np.max(time_diffs),
                'coincidence_rate': len(coincidences) / max(len(time_diffs), 1)
            }
            
            return stats
            
        except Exception as e:
            print(f"Erro no cálculo de estatísticas: {e}")
            return {
                'total_coincidences': len(coincidences),
                'mean_time_diff': 0,
                'std_time_diff': 0,
                'min_time_diff': 0,
                'max_time_diff': 0,
                'coincidence_rate': 0
            }
    
    def calculate_fft_manual(self, data, sample_rate):
        """
        Calcula FFT manualmente sem scipy
        """
        n = len(data)
        if n == 0:
            return np.array([]), np.array([])
        
        # FFT manual usando numpy
        fft_result = np.fft.fft(data)
        freqs = np.fft.fftfreq(n, 1/sample_rate)
        
        # Pegar apenas a parte positiva
        positive_freqs = freqs[:n//2]
        positive_fft = np.abs(fft_result[:n//2])
        
        return positive_freqs, positive_fft
    
    def plot_results(self, t, data_ch1, data_ch2, peaks_ch1, peaks_ch2, coincidences):
        """
        Plota os resultados da análise
        """
        try:
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
            
            # Plot dados brutos
            ax1.plot(t, data_ch1, 'b-', label='Canal 1', alpha=0.7, linewidth=1)
            ax1.plot(t, data_ch2, 'r-', label='Canal 2', alpha=0.7, linewidth=1)
            
            if len(peaks_ch1) > 0:
                ax1.plot(t[peaks_ch1], data_ch1[peaks_ch1], 'bo', label='Picos Ch1', markersize=3)
            if len(peaks_ch2) > 0:
                ax1.plot(t[peaks_ch2], data_ch2[peaks_ch2], 'ro', label='Picos Ch2', markersize=3)
                
            ax1.set_xlabel('Tempo (s)')
            ax1.set_ylabel('Amplitude (V)')
            ax1.set_title('Dados dos Canais com Picos Detectados')
            ax1.legend()
            ax1.grid(True)
            
            # Plot espectro de frequência manual
            actual_fs = 1 / (t[1] - t[0]) if len(t) > 1 else self.sample_rate
            
            # Calcular FFT para canal 1
            freqs1, fft1 = self.calculate_fft_manual(data_ch1, actual_fs)
            if len(freqs1) > 0:
                ax2.semilogy(freqs1, fft1, 'b-', label='Canal 1')
            
            # Calcular FFT para canal 2
            freqs2, fft2 = self.calculate_fft_manual(data_ch2, actual_fs)
            if len(freqs2) > 0:
                ax2.semilogy(freqs2, fft2, 'r-', label='Canal 2', alpha=0.7)
            
            ax2.set_xlabel('Frequência (Hz)')
            ax2.set_ylabel('Magnitude FFT')
            ax2.set_title('Espectro de Frequência (FFT)')
            ax2.legend()
            ax2.grid(True)
            ax2.set_xlim(0, min(10e6, actual_fs/2))  # Limitar a 10 MHz para melhor visualização
            
            # Plot histograma de diferenças temporais
            if coincidences:
                time_diffs = [abs(t[peaks_ch1[i]] - t[peaks_ch2[j]]) for i, j in coincidences]
                ax3.hist([td * 1e9 for td in time_diffs], bins=30, alpha=0.7, edgecolor='black')
                ax3.axvline(self.time_window * 1e9, color='red', linestyle='--', 
                           label=f'Janela de 5 ns')
                ax3.set_xlabel('Diferença Temporal (ns)')
                ax3.set_ylabel('Contagem')
                ax3.set_title('Histograma de Diferenças Temporais nas Coincidências')
                ax3.legend()
                ax3.grid(True)
            else:
                ax3.text(0.5, 0.5, 'Nenhuma coincidência encontrada', 
                        horizontalalignment='center', verticalalignment='center',
                        transform=ax3.transAxes)
                ax3.set_title('Histograma de Diferenças Temporais')
                ax3.grid(True)
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            print(f"Erro no plotting: {e}")
    
    def run_analysis(self, num_acquisitions=3):
        """
        Executa análise completa múltiplas vezes
        """
        all_stats = []
        
        print("Iniciando análise de coincidências...")
        print(f"Janela temporal: {self.time_window*1e9:.1f} ns")
        print("-" * 50)
        
        for i in range(num_acquisitions):
            print(f"Aquisição {i+1}/{num_acquisitions}")
            
            # Adquirir dados
            t, data_ch1, data_ch2 = self.acquire_data()
            
            if data_ch1 is None or data_ch2 is None:
                print("  Erro na aquisição de dados. Pulando...")
                continue
            
            # Analisar coincidências
            coincidences, coincident_freqs, time_diffs, peaks_ch1, peaks_ch2 = self.find_coincidences(
                t, data_ch1, data_ch2
            )
            
            # Calcular estatísticas
            stats = self.analyze_coincidence_statistics(coincidences, time_diffs)
            all_stats.append(stats)
            
            print(f"  Coincidências encontradas: {stats['total_coincidences']}")
            if stats['total_coincidences'] > 0:
                print(f"  Dif. temporal média: {stats['mean_time_diff']*1e9:.2f} ns")
                print(f"  Taxa de coincidência: {stats['coincidence_rate']:.3f}")
                
                # Mostrar algumas frequências coincidentes
                for idx, (freq1, freq2) in enumerate(coincident_freqs[:3]):
                    print(f"  Coincidência {idx+1}: {freq1/1e6:.2f} MHz vs {freq2/1e6:.2f} MHz")
            print()
            
            # Plotar resultados da primeira aquisição com coincidências
            if i == 0 and stats['total_coincidences'] > 0:
                self.plot_results(t, data_ch1, data_ch2, peaks_ch1, peaks_ch2, coincidences)
        
        return all_stats
    
    def close(self):
        """
        Fecha a conexão com a Red Pitaya
        """
        try:
            self.rp.close()
            print("Conexão com Red Pitaya fechada")
        except:
            pass

# Função auxiliar para análise detalhada
def detailed_coincidence_analysis(analyzer):
    """
    Executa uma análise detalhada de coincidências
    """
    print("Executando análise detalhada de coincidências...")
    
    # Configurar aquisição
    analyzer.setup_acquisition(decimation=8, trigger_level=0.05)
    
    # Adquirir dados
    t, data_ch1, data_ch2 = analyzer.acquire_data()
    
    if data_ch1 is None or data_ch2 is None:
        print("Falha na aquisição de dados")
        return
    
    # Encontrar picos
    peaks_ch1 = analyzer.find_peaks(data_ch1)
    peaks_ch2 = analyzer.find_peaks(data_ch2)
    
    print(f"Picos encontrados - Canal 1: {len(peaks_ch1)}, Canal 2: {len(peaks_ch2)}")
    
    if len(peaks_ch1) > 1 and len(peaks_ch2) > 1:
        # Calcular frequências
        freqs_ch1 = analyzer.calculate_frequencies(t, peaks_ch1)
        freqs_ch2 = analyzer.calculate_frequencies(t, peaks_ch2)
        
        print(f"Frequências calculadas - Canal 1: {len(freqs_ch1)}, Canal 2: {len(freqs_ch2)}")
        
        if len(freqs_ch1) > 0 and len(freqs_ch2) > 0:
            print(f"Frequência média - Canal 1: {np.mean(freqs_ch1)/1e6:.2f} MHz")
            print(f"Frequência média - Canal 2: {np.mean(freqs_ch2)/1e6:.2f} MHz")
            
            # Analisar coincidências
            coincidences, coincident_freqs, time_diffs, _, _ = analyzer.find_coincidences(
                t, data_ch1, data_ch2
            )
            
            print(f"Coincidências encontradas: {len(coincidences)}")
            
            for i, ((freq1, freq2), time_diff) in enumerate(zip(coincident_freqs, time_diffs)):
                print(f"Coincidência {i+1}:")
                print(f"  Frequência Ch1: {freq1/1e6:.3f} MHz")
                print(f"  Frequência Ch2: {freq2/1e6:.3f} MHz")
                print(f"  Diferença: {abs(freq1-freq2)/1e3:.1f} kHz")
                print(f"  Tempo: {time_diff*1e9:.2f} ns")
                print()

# Exemplo de uso
if __name__ == "__main__":
    # Configurações
    RP_IP = '192.168.1.100'  # Ajuste para o IP da sua Red Pitaya
    RP_PORT = 5000
    NUM_ACQUISITIONS = 3
    
    # Inicializar analisador
    analyzer = FrequencyCoincidenceAnalyzer(ip_address=RP_IP, port=RP_PORT)
    
    try:
        # Executar análise
        stats = analyzer.run_analysis(num_acquisitions=NUM_ACQUISITIONS)
        
        # Estatísticas finais
        print("=" * 60)
        print("ESTATÍSTICAS FINAIS:")
        print("=" * 60)
        
        total_coincidences = sum(s['total_coincidences'] for s in stats)
        valid_stats = [s for s in stats if s['total_coincidences'] > 0]
        
        if valid_stats:
            avg_time_diff = np.mean([s['mean_time_diff'] for s in valid_stats])
            avg_rate = np.mean([s['coincidence_rate'] for s in valid_stats])
            
            print(f"Total de coincidências: {total_coincidences}")
            print(f"Média das diferenças temporais: {avg_time_diff*1e9:.2f} ns")
            print(f"Taxa média de coincidência: {avg_rate:.3f}")
            
            # Executar análise detalhada se houver coincidências
            if total_coincidences > 0:
                print("\n" + "=" * 60)
                detailed_coincidence_analysis(analyzer)
        else:
            print("Nenhuma coincidência encontrada nas aquisições")
        
    except KeyboardInterrupt:
        print("\nAnálise interrompida pelo usuário")
    except Exception as e:
        print(f"Erro durante a execução: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        analyzer.close()
        print("Análise concluída.")
import numpy as np

class math (object):
    def calcular_fft(sinal, rbw):
        
        sample_rate = 125e6
        ts = 1/sample_rate
        
        n = len(sinal)
        
        # Calcula o tamanho necessário da FFT para atingir a RBW desejada
        n_rbw = int(sample_rate / rbw)
        n_rbw = min(n_rbw, n)  # Não pode ser maior que o buffer
        n_rbw = max(n_rbw, 2)  # Pelo menos 2 pontos
        
        # Recorta o sinal para o novo tamanho
        sinal_recortado = sinal[:n_rbw]
        
        window = np.hanning(n_rbw)
        fft_result = np.fft.fft(sinal_recortado * window)
        fft_freq = np.fft.fftfreq(n_rbw, d=ts)[:n_rbw//2]
        fft_db = 20 * np.log10(np.abs(fft_result[:n_rbw//2]) + 1e-10)
        
        return fft_freq, fft_db
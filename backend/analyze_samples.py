import soundfile as sf
import numpy as np
import os

def analyze_sample(filename):
    path = os.path.join("irs", filename)
    if not os.path.exists(path):
        print(f"File {filename} not found.")
        return
        
    data, fs = sf.read(path)
    if len(data.shape) > 1: data = data[:, 0]
    
    # Use the same NSDF logic or just a simple FFT peak
    fft = np.fft.rfft(data)
    freqs = np.fft.rfftfreq(len(data), 1/fs)
    peak_idx = np.argmax(np.abs(fft))
    peak_freq = freqs[peak_idx]
    
    print(f"Sample: {filename}")
    print(f"Peak Frequency: {peak_freq:.2f} Hz")

if __name__ == "__main__":
    analyze_sample("laser.wav")
    analyze_sample("fart_resonance.wav")

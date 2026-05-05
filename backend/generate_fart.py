import numpy as np
import soundfile as sf
import os

def generate_fart_ir(filename="fart_resonance.wav", duration=2.5, sr=44100):
    t = np.linspace(0, duration, int(sr * duration))
    
    # Fundamental frequency (low rumble) with massive wobbling
    f0 = 30 + 50 * np.abs(np.sin(2 * np.pi * 3 * t))
    
    # Sawtooth wave with duty cycle modulation for the "flapping"
    audio = np.mod(t * f0, 1.0) - 0.5
    
    # Add intense high frequency "splatter" noise spikes
    for _ in range(10):
        pos = np.random.uniform(0, duration)
        spike = np.exp(-50 * (t - pos)**2) * np.random.normal(0, 1.0, len(t))
        audio += spike
    
    # Add a wet/squelchy resonance
    audio += 0.5 * np.sin(2 * np.pi * 180 * t) * (np.sin(2 * np.pi * 8 * t) > 0.5)
    
    # Normalize to 0dB to ensure it's LOUD
    audio = audio / (np.max(np.abs(audio)) + 1e-9)
    
    path = os.path.join("irs", filename)
    if not os.path.exists("irs"):
        os.makedirs("irs")
    sf.write(path, audio, sr)
    print(f"Generated {path}")

if __name__ == "__main__":
    generate_fart_ir()

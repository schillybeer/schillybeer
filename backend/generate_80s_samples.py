import numpy as np
import soundfile as sf
import os

def save_sample(filename, audio, sr=44100):
    path = os.path.join("irs", filename)
    if not os.path.exists("irs"):
        os.makedirs("irs")
    # Normalize
    audio = audio / (np.max(np.abs(audio)) + 1e-9)
    sf.write(path, audio, sr)
    print(f"Generated {path}")

def generate_synth_stab(duration=0.5, sr=44100):
    t = np.linspace(0, duration, int(sr * duration))
    # Detuned sawtooths
    f = 110 # A2
    audio = (np.mod(t * f, 1.0) - 0.5) + \
            0.5 * (np.mod(t * (f * 1.01), 1.0) - 0.5) + \
            0.3 * (np.mod(t * (f * 0.99), 1.0) - 0.5)
    
    # Exponential decay
    envelope = np.exp(-10 * t)
    return audio * envelope

def generate_orch_hit(duration=0.6, sr=44100):
    t = np.linspace(0, duration, int(sr * duration))
    # Mix of many frequencies for that "hit" feel
    freqs = [110, 138.59, 164.81, 220, 277.18, 329.63, 440] # A Major cluster
    audio = np.zeros_like(t)
    for i, f in enumerate(freqs):
        # mix of sine and saw
        audio += (1.0 / (i+1)) * np.sin(2 * np.pi * f * t)
        audio += (0.5 / (i+1)) * (np.mod(t * f, 1.0) - 0.5)
    
    # Add noise burst at the start
    noise = np.random.normal(0, 0.2, len(t)) * np.exp(-50 * t)
    audio += noise
    
    # Sharp decay
    envelope = np.exp(-8 * t)
    return audio * envelope

def generate_hey_hit(duration=0.4, sr=44100):
    t = np.linspace(0, duration, int(sr * duration))
    # A "hey" is roughly a vocal-filtered noise burst
    # Formants for 'e' are roughly 500Hz, 1700Hz, 2300Hz
    noise = np.random.normal(0, 1.0, len(t))
    
    # Simple resonant filtering simulation via sine modulation
    audio = noise * (np.sin(2 * np.pi * 500 * t) + np.sin(2 * np.pi * 1700 * t))
    
    # Envelope with quick attack and decay
    envelope = np.exp(-200 * t) # attack
    envelope = np.minimum(envelope, np.exp(-15 * (t - 0.05)))
    
    # Actually just use a simpler envelope for that '80s gating' feel
    envelope = np.ones_like(t)
    envelope[int(sr*0.3):] = 0
    envelope[:int(sr*0.01)] = np.linspace(0, 1, int(sr*0.01))
    envelope *= np.exp(-10 * t)
    
    return audio * envelope

if __name__ == "__main__":
    save_sample("synth_stab.wav", generate_synth_stab())
    save_sample("orch_hit.wav", generate_orch_hit())
    save_sample("hey_hit.wav", generate_hey_hit())

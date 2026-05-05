import numpy as np
import soundfile as sf
import os

def save_sample(filename, audio, sr=44100):
    path = os.path.join("irs", filename)
    if not os.path.exists("irs"):
        os.makedirs("irs")
    # Normalize to -1dB
    audio = audio / (np.max(np.abs(audio)) + 1e-9) * 0.9
    sf.write(path, audio, sr)
    print(f"Generated {path}")

# --- ARCADE PACK ---
def gen_laser(duration=0.3, sr=44100):
    t = np.linspace(0, duration, int(sr * duration))
    f = 2000 * np.exp(-15 * t) # Rapid pitch drop
    return np.sin(2 * np.pi * f * t) * np.exp(-5 * t)

def gen_explosion(duration=0.8, sr=44100):
    t = np.linspace(0, duration, int(sr * duration))
    noise = np.random.normal(0, 1.0, len(t))
    # Low-pass filter effect via envelope
    env = np.exp(-4 * t)
    return noise * env

def gen_coin(duration=0.2, sr=44100):
    t = np.linspace(0, duration, int(sr * duration))
    # Two square waves (fifths)
    f1, f2 = 987.77, 1318.51 # B5, E6
    audio = (np.sin(2 * np.pi * f1 * t) > 0).astype(float)
    audio += (np.sin(2 * np.pi * f2 * (t - 0.05)) > 0).astype(float) * (t > 0.05)
    return audio * np.exp(-10 * t)

# --- VOCAL PACK ---
def gen_wow(duration=0.5, sr=44100):
    t = np.linspace(0, duration, int(sr * duration))
    f = 200 + 400 * np.sin(np.pi * t / duration) # Formant-like wobble
    audio = np.sin(2 * np.pi * f * t) * np.exp(-5 * t)
    return audio + 0.2 * np.random.normal(0, 1, len(t)) * np.exp(-20 * t)

def gen_robot_hey(duration=0.4, sr=44100):
    t = np.linspace(0, duration, int(sr * duration))
    audio = (np.mod(t * 150, 1.0) - 0.5) # Buzzer
    audio *= (np.sin(2 * np.pi * 800 * t) + np.sin(2 * np.pi * 1200 * t))
    return audio * np.exp(-10 * t)

# --- INSTRUMENT PACK ---
def gen_lofi_piano(duration=1.0, sr=44100):
    t = np.linspace(0, duration, int(sr * duration))
    f = 261.63 # C4
    audio = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 2 * f * t)
    return audio * np.exp(-3 * t)

def gen_lofi_strings(duration=1.5, sr=44100):
    t = np.linspace(0, duration, int(sr * duration))
    f = 196.00 # G3
    audio = (np.mod(t * f, 1.0) - 0.5) + 0.1 * np.random.normal(0, 1, len(t))
    # Slow attack
    attack = np.minimum(1.0, t / 0.5)
    return audio * attack * np.exp(-0.5 * t)

# --- DRUM PACK ---
def gen_808_kick(duration=0.6, sr=44100):
    t = np.linspace(0, duration, int(sr * duration))
    f = 150 * np.exp(-25 * t) + 40 # Pitch drop
    return np.sin(2 * np.pi * f * t) * np.exp(-6 * t)

def gen_808_snare(duration=0.3, sr=44100):
    t = np.linspace(0, duration, int(sr * duration))
    noise = np.random.normal(0, 1.0, len(t))
    tone = np.sin(2 * np.pi * 180 * t) * np.exp(-20 * t)
    return (noise * np.exp(-15 * t) + tone)

def gen_cowbell(duration=0.4, sr=44100):
    t = np.linspace(0, duration, int(sr * duration))
    f1, f2 = 540, 800
    audio = (np.sin(2 * np.pi * f1 * t) > 0).astype(float) + (np.sin(2 * np.pi * f2 * t) > 0).astype(float)
    return audio * np.exp(-10 * t)

if __name__ == "__main__":
    save_sample("laser.wav", gen_laser())
    save_sample("explosion.wav", gen_explosion())
    save_sample("coin.wav", gen_coin())
    save_sample("wow.wav", gen_wow())
    save_sample("robot_hey.wav", gen_robot_hey())
    save_sample("lofi_piano.wav", gen_lofi_piano())
    save_sample("lofi_strings.wav", gen_lofi_strings())
    save_sample("808_kick.wav", gen_808_kick())
    save_sample("808_snare.wav", gen_808_snare())
    save_sample("cowbell.wav", gen_cowbell())

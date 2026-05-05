import numpy as np
import soundfile as sf
import os

# Create irs dir if not exists
os.makedirs('irs', exist_ok=True)

# 44.1kHz sample rate, length 0.05 seconds (50ms)
fs = 44100
t = np.linspace(0, 0.05, int(fs * 0.05), endpoint=False)

# Generate a synthetic impulse (white noise that decays exponentially)
noise = np.random.randn(len(t))
decay = np.exp(-t * 200)
impulse = noise * decay

# Very basic low-pass filter (moving average) to simulate a guitar cab
window_size = 5
filtered_impulse = np.convolve(impulse, np.ones(window_size)/window_size, mode='same')

# Normalize
filtered_impulse = filtered_impulse / np.max(np.abs(filtered_impulse))

# Write to WAV file
sf.write('irs/vintage_4x12.wav', filtered_impulse.astype(np.float32), fs)
print("Synthesized placeholder Cabinet IR saved to irs/vintage_4x12.wav!")

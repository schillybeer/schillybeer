import sounddevice as sd
import numpy as np
import time
from audio_engine import AudioEngine

def run_diagnostic(duration=5):
    print(f"--- RIG DIAGNOSTICS STARTING IN 2 SECONDS ---")
    print("Prepare to play a sustained G note (3rd fret, bottom string)...")
    time.sleep(2)
    
    print(f"CAPTURING {duration} SECONDS...")
    fs = 44100
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    
    # We also want to see what the engine thinks the pitch is
    engine = AudioEngine()
    pitches = []
    
    start_time = time.time()
    while time.time() - start_time < duration:
        # Check current engine state (we'd need a way to peek at the real engine, 
        # but for now let's just analyze the recording we are making)
        time.sleep(0.1)
    
    sd.wait()
    print("CAPTURE COMPLETE. ANALYZING...")
    
    # Analyze the recording
    audio = recording.flatten()
    # Simple FFT to find the dominant frequency
    fft = np.fft.rfft(audio)
    freqs = np.fft.rfftfreq(len(audio), 1/fs)
    peak_idx = np.argmax(np.abs(fft))
    peak_freq = freqs[peak_idx]
    
    print(f"\n--- ANALYSIS RESULTS ---")
    print(f"Dominant Frequency Captured: {peak_freq:.2f} Hz")
    
    # Note mapping
    def freq_to_note(f):
        if f <= 0: return "None"
        n = 12 * np.log2(f / 440.0) + 69
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        midi = int(round(n))
        return f"{notes[midi % 12]}{midi // 12 - 1}"

    print(f"Closest Musical Note: {freq_to_note(peak_freq)}")
    print(f"Energy Level: {np.max(np.abs(audio)):.4f}")
    
    if peak_freq < 70:
        print("WARNING: Captured frequency is very low. Possible hum or noise interference.")
    elif peak_freq > 1200:
        print("WARNING: Captured frequency is very high. Possible harmonic interference.")
    else:
        print("SUCCESS: Signal within expected guitar range.")

if __name__ == "__main__":
    run_diagnostic()

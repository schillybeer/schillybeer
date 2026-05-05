import os
import time
import soundfile as sf
import sounddevice as sd

def play_samples():
    irs_dir = "irs"
    samples = [f for f in os.listdir(irs_dir) if f.endswith(".wav")]
    samples.sort()
    
    print(f"--- Previewing {len(samples)} Samples ---")
    for sample in samples:
        path = os.path.join(irs_dir, sample)
        print(f"Playing: {sample}...")
        data, sr = sf.read(path)
        sd.play(data, sr)
        # Wait for the sample to finish plus a small gap
        time.sleep(len(data) / sr + 0.2)
    print("Done!")

if __name__ == "__main__":
    play_samples()

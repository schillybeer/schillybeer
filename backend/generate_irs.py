import numpy as np
import soundfile as sf
import os

def generate_ir(filename, duration=1.0, sr=44100):
    t = np.linspace(0, duration, int(sr * duration))
    
    if filename == "metallic_clang.wav":
        # Impact followed by inharmonic sine waves
        impact = np.exp(-100 * t) * np.random.normal(0, 0.1, len(t))
        body = np.exp(-5 * t) * (
            np.sin(2 * np.pi * 440 * t) + 
            np.sin(2 * np.pi * 987 * t) + 
            np.sin(2 * np.pi * 1532 * t)
        )
        audio = impact + 0.5 * body
        
    elif filename == "robotic_drone.wav":
        # Glitchy square waves with noise
        audio = np.exp(-2 * t) * (
            np.sign(np.sin(2 * np.pi * 100 * t * np.sin(2 * np.pi * 2 * t))) +
            0.5 * np.random.normal(0, 0.2, len(t))
        )
        
    elif filename == "washing_machine.wav":
        # Low rumbly noise with mechanical resonance
        low_rumble = np.exp(-1 * t) * np.sin(2 * np.pi * 50 * t)
        sloshing = np.exp(-2 * t) * np.random.normal(0, 0.3, len(t))
        # Add a periodic metallic "thump"
        thump = np.zeros_like(t)
        for i in range(0, len(t), int(sr * 0.5)):
            thump[i:i+1000] = 0.5
        audio = low_rumble + sloshing + 0.2 * thump
        
    elif filename == "alien_chatter.wav":
        # High frequency FM synthesis noise
        audio = np.exp(-3 * t) * np.sin(2 * np.pi * 2000 * t + 50 * np.sin(2 * np.pi * 100 * t))
        audio *= np.random.normal(0, 0.5, len(t))

    # Normalize
    audio = audio / np.max(np.abs(audio))
    
    path = os.path.join("irs", filename)
    sf.write(path, audio, sr)
    print(f"Generated {path}")

if __name__ == "__main__":
    if not os.path.exists("irs"):
        os.makedirs("irs")
    
    generate_ir("metallic_clang.wav")
    generate_ir("robotic_drone.wav")
    generate_ir("washing_machine.wav")
    generate_ir("alien_chatter.wav")

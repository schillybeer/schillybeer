import numpy as np
import sys
import os

# Ensure we can import backend modules
sys.path.append(os.path.dirname(__file__))

from audio_engine import AudioEngine, AsymmetricDistortion, PowerAmpSag
from tone_library import ARTIST_PRESETS
from pedalboard import Limiter

def test_preset(engine, preset_name, preset_data):
    print(f"\n--- Testing Preset: {preset_name} ---")
    
    # 1. Generate a test signal (e.g., a burst of pink noise or a chord simulation)
    # 128 frames at 44100Hz = ~2.9ms. Let's process a few blocks to allow filters to settle.
    # We'll use a simple 440Hz sine wave + 880Hz + 1320Hz to simulate a complex tone.
    sample_rate = 44100
    blocksize = 128
    num_blocks = 10
    total_frames = blocksize * num_blocks
    
    t = np.linspace(0, total_frames / sample_rate, total_frames, endpoint=False)
    test_signal = np.sin(2 * np.pi * 440 * t) + 0.5 * np.sin(2 * np.pi * 880 * t) + 0.25 * np.sin(2 * np.pi * 1320 * t)
    test_signal = test_signal * 0.1 # -20dBFS input to avoid clipping before drive
    
    # Reshape into blocks
    blocks = np.array_split(test_signal, num_blocks)
    
    # 2. Build the board
    success = engine.build_dynamic_board(preset_data["chain"])
    if not success:
        print("FAILED to build board.")
        return
        
    print(f"Chain length: {len(engine.effects_chain)} plugins.")
    
    # Print out the actual types in the chain
    plugin_types = [type(p).__name__ for p in engine.effects_chain]
    print(f"Chain composition: {plugin_types}")
    
    # 3. Process the signal
    processed_signal = []
    
    # We must manually process using the logic from audio_callback
    for block in blocks:
        mono_input = block.astype(np.float32)
        processed = mono_input.copy()
        
        # Simulate NDE (Neural Dynamic Expression)
        rms = float(np.sqrt(np.mean(mono_input**2)))
        for plugin in engine.effects_chain:
            if hasattr(plugin, 'drive_db') and not isinstance(plugin, AsymmetricDistortion): # Asymmetric doesn't have drive_db settable the same way dynamically yet? Wait, yes it does.
                # Actually, NDE logic in callback modifies drive_db.
                try:
                    plugin.drive_db = 10 + (rms * 60 * 0.5) # Assuming sensitivity 0.5
                except:
                    pass
                    
        # Iterate through Hybrid Loop
        for fx in engine.effects_chain:
            try:
                if isinstance(fx, (AsymmetricDistortion, PowerAmpSag)):
                    processed = fx.process(processed)
                else:
                    dry = np.expand_dims(processed, axis=0).astype(np.float32)
                    wet = fx(dry, sample_rate=float(sample_rate), reset=False)
                    processed = wet[0]
            except Exception as e:
                print(f"ERROR processing {type(fx).__name__}: {e}")
                
        processed_signal.extend(processed.tolist())
        
    processed_signal = np.array(processed_signal)
    
    # 4. Analyze Output
    rms_out = np.sqrt(np.mean(processed_signal**2))
    peak_out = np.max(np.abs(processed_signal))
    
    # Simple spectral centroid proxy: zero crossings
    zero_crossings = np.where(np.diff(np.sign(processed_signal)))[0]
    
    print(f"Output RMS: {rms_out:.5f} | Peak: {peak_out:.5f} | Zero Crossings: {len(zero_crossings)}")
    
    # If the output is identical to input, or exactly zero, something is wrong.
    rms_in = np.sqrt(np.mean(test_signal**2))
    print(f"Input RMS:  {rms_in:.5f}")
    if abs(rms_out - rms_in) < 1e-5:
         print("WARNING: Output RMS is identical to Input RMS. Is the chain doing anything?")
    if rms_out < 1e-6:
         print("WARNING: Output is silent!")


if __name__ == "__main__":
    print("Initializing Audio Engine for Diagnostics...")
    # Initialize without starting the audio stream
    engine = AudioEngine()
    engine.nde_enabled = False # Test pure chain first
    
    for artist, data in ARTIST_PRESETS.items():
        test_preset(engine, artist, data)
    
    print("\nDiagnostics complete.")

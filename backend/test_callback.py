import numpy as np
from audio_engine import engine

# Simulate building the board
chain = [{'effect': 'Mix', 'chains': [[{'effect': 'PitchShift', 'semitones': 12}], [{'effect': 'PitchShift', 'semitones': -12}]]}, {'effect': 'Chorus', 'rate_hz': 0.5, 'depth': 0.7, 'mix': 0.8}, {'effect': 'Reverb', 'room_size': 0.6, 'wet_level': 0.5, 'dry_level': 0.5}]
engine.build_dynamic_board(chain)

# Simulate audio callback
indata = np.zeros((128, 2), dtype=np.float32)
outdata = np.zeros((128, 2), dtype=np.float32)

try:
    engine.audio_callback(indata, outdata, 128, None, None)
    print("Callback succeeded!")
except Exception as e:
    print(f"Callback crashed: {e}")

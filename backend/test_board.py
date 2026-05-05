import numpy as np
from pedalboard import Pedalboard, PitchShift, Reverb, Limiter

board = Pedalboard([
    PitchShift(semitones=12),
    PitchShift(semitones=-12),
    Reverb(room_size=0.9),
    Limiter(threshold_db=-1.0)
])

dry = np.zeros((1, 128), dtype=np.float32)

print("Running with reset=True")
wet1 = board(dry, 44100, reset=True)
print(wet1.shape)

print("Running with reset=False")
wet2 = board(dry, 44100, reset=False)
print(wet2.shape)

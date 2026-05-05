from pedalboard import Convolution
import os

ir_path = os.path.join("irs", "vintage_4x12.wav")
try:
    c = Convolution(ir_path, mix=1.0)
    print("Success with mix=1.0")
except TypeError as e:
    print(f"Failed with mix=1.0: {e}")

try:
    c = Convolution(ir_path, 1.0)
    print("Success with positional 1.0")
except TypeError as e:
    print(f"Failed with positional 1.0: {e}")

import os
from pedalboard import load_plugin

path = r"C:\Program Files\Common Files\VST3\NeuralAmpModeler.vst3"
print(f"Loading plugin from {path}...")
try:
    vst = load_plugin(path)
    print("Parameters available:")
    for param_name, param_obj in vst.parameters.items():
        print(f" - {param_name}")
except Exception as e:
    print(f"Failed: {e}")

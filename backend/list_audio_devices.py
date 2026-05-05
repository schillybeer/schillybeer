import sounddevice as sd

print("--- Available Audio Devices ---")
devices = sd.query_devices()
for i, dev in enumerate(devices):
    print(f"[{i}] {dev['name']} (Inputs: {dev['max_input_channels']}, Outputs: {dev['max_output_channels']})")

print("\n--- Default Devices ---")
default_input = sd.query_devices(kind='input')
default_output = sd.query_devices(kind='output')
print(f"Default Input: {default_input['name']}")
print(f"Default Output: {default_output['name']}")

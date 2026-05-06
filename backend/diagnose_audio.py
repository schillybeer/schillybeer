import sounddevice as sd
import json

def get_audio_diagnostics():
    devices = sd.query_devices()
    hostapis = sd.query_hostapis()
    
    print("--- AUDIO HOST APIS ---")
    for i, api in enumerate(hostapis):
        print(f"[{i}] {api['name']} (Default In: {api['default_input_device']}, Default Out: {api['default_output_device']})")
    
    print("\n--- AUDIO DEVICES ---")
    digitech_in = None
    digitech_out = None
    
    for i, dev in enumerate(devices):
        name = dev['name']
        api_index = dev['hostapi']
        api_name = hostapis[api_index]['name']
        
        # Look for Digitech
        is_digitech = "digitech" in name.lower() or "usb audio" in name.lower()
        marker = " [MATCH!]" if is_digitech else ""
        
        print(f"[{i}] {name} ({api_name}) - In: {dev['max_input_channels']}, Out: {dev['max_output_channels']}{marker}")
        
        if is_digitech:
            if dev['max_input_channels'] > 0 and digitech_in is None:
                digitech_in = i
            if dev['max_output_channels'] > 0 and digitech_out is None:
                digitech_out = i

    print("\n--- SELECTION LOGIC ---")
    if digitech_in is not None and digitech_out is not None:
        print(f"IDENTIFIED DIGITECH: Input={digitech_in}, Output={digitech_out}")
    else:
        print("DIGITECH NOT FOUND BY NAME. Falling back to system defaults.")
        print(f"System Default Input: {sd.default.device[0]}")
        print(f"System Default Output: {sd.default.device[1]}")

if __name__ == "__main__":
    get_audio_diagnostics()

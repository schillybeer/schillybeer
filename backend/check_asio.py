import sounddevice as sd

def list_devices():
    print("-" * 50)
    print("SCHILLYBEER AUDIO DIAGNOSTICS")
    print("-" * 50)
    
    apis = sd.query_hostapis()
    asio_found = False
    
    print("\n--- Available Host APIs ---")
    for i, api in enumerate(apis):
        print(f"[{i}] {api['name']} (Devices: {len(api['devices'])})")
        if 'ASIO' in api['name']:
            asio_found = True
            
    if asio_found:
        print("\n[OK] ASIO DRIVERS DETECTED!")
    else:
        print("\n[!] NO ASIO DETECTED. Using WASAPI (higher latency).")
        print("Tip: Install ASIO4ALL or your interface's official drivers for pro performance.")

    print("\n--- Device List ---")
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        api_name = apis[dev['hostapi']]['name']
        print(f"{i}: {dev['name']} ({api_name})")
        print(f"   Inputs: {dev['max_input_channels']}, Outputs: {dev['max_output_channels']}")

if __name__ == "__main__":
    list_devices()

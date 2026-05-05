import sounddevice as sd

print("--- Checking ASIO Drivers ---")
asio_found = False
for api in sd.query_hostapis():
    print(f"Host API: {api['name']}")
    if 'ASIO' in api['name']:
        asio_found = True

if asio_found:
    print("\nSUCCESS: ASIO Driver is detected by Python!")
else:
    print("\nERROR: ASIO is still not detected.")

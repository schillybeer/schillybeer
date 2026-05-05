import requests
import time

def check_tuner():
    print("Checking Tuner API...")
    try:
        for _ in range(5):
            response = requests.get("http://127.0.0.1:8000/api/tuner")
            print(f"Status: {response.status_code}, Data: {response.json()}")
            time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_tuner()

import requests

data = {"prompt": "fart noise"}
response = requests.post("http://127.0.0.1:8000/api/tone/prompt", json=data)
print(response.json())

import requests

data = {"prompt": "12 string guitar"}
response = requests.post("http://127.0.0.1:8000/api/tone/prompt", json=data)
print(response.json())

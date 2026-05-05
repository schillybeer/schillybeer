import requests

data = {"prompt": "heavy metal distortion with massive reverb"}
response = requests.post("http://127.0.0.1:8000/api/tone/prompt", json=data)
print(response.json())

import requests

url = "http://127.0.0.1:8000/chat"
data = {"prompt": "Bonjour Ollama, raconte-moi une blague courte."}

response = requests.post(url, json=data)
print(response.json())


import requests
import json

url = "http://localhost:5000/chat"
data = {"message": "hello", "user_id": "test123"}

print("Sending request to:", url)
print("Data:", data)

try:
    import time
    start_time = time.time()
    response = requests.post(url, json=data, timeout=180)
    elapsed = time.time() - start_time
    print(f"Status: {response.status_code} (耗时: {elapsed:.1f}秒)")
    print("Response:", response.json())
except Exception as e:
    print("Error:", e)

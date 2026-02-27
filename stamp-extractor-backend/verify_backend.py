import requests
import json
import os

url = "http://127.0.0.1:8000/extract-stamp"
file_path = "/Users/shashank/Documents/GitHub/prostruct/Stamped_Plans (1).pdf"

if not os.path.exists(file_path):
    print(f"Error: File not found at {file_path}")
    exit(1)

print(f"Testing extraction on: {file_path}")
with open(file_path, "rb") as f:
    # Page 1 (0-indexed might be 0, but the previous test used 1)
    files = {"file": ("Stamped_Plans.pdf", f, "application/pdf")}
    data = {"page": 4} 
    print("Sending request to /extract-stamp (Page 4)...")
    response = requests.post(url, files=files, data=data)

if response.status_code == 200:
    print("Success!")
    res_data = response.json()
    print(json.dumps(res_data, indent=2))
else:
    print(f"Error {response.status_code}: {response.text}")

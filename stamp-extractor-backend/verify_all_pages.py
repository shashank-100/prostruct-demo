import requests
import json
import os

url = "http://127.0.0.1:8000/extract-stamp"
file_path = "/Users/shashank/Documents/GitHub/prostruct/Stamped_Plans (1).pdf"

if not os.path.exists(file_path):
    print(f"Error: File not found at {file_path}")
    exit(1)

print(f"Testing extraction on: {file_path}")

for page_idx in range(4):
    print(f"\n--- Testing Page {page_idx + 1} (index {page_idx}) ---")
    try:
        with open(file_path, "rb") as f:
            files = {"file": ("Stamped_Plans.pdf", f, "application/pdf")}
            data = {"page": page_idx} 
            response = requests.post(url, files=files, data=data, timeout=60)

        if response.status_code == 200:
            res_data = response.json()
            # print(json.dumps(res_data, indent=2))
            stamps = res_data.get("stamps", [])
            print(f"Found {len(stamps)} stamps:")
            for s in stamps:
                print(f"  - Name: {s.get('engineer_name')}, License: {s.get('license_number')}")
        else:
            print(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

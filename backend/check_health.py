import requests
import sys

def check_server():
    url = "http://127.0.0.1:8000/admin/login/"
    print(f"Checking {url}...")
    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Server is UP.")
        else:
            print("Server is UP but returned non-200.")
    except Exception as e:
        print(f"Server appears DOWN. Error: {e}")

if __name__ == "__main__":
    check_server()

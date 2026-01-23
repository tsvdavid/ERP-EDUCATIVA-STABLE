import requests
import sys
import time

BASE_URL = "http://localhost:8000"

def test_reset():
    # 1. Login to get token
    login_url = f"{BASE_URL}/api/token/"
    credentials = {
        "username": "admin",
        "password": "admin123"
    }
    
    print(f"Attempting login with {credentials}...")
    try:
        response = requests.post(login_url, json=credentials)
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Is it running?")
        sys.exit(1)
        
    if response.status_code != 200:
        print(f"Login failed: {response.status_code} - {response.text}")
        sys.exit(1)
        
    token = response.json().get('access')
    if not token:
        print("No access token received.")
        sys.exit(1)
    
    print("Login successful. Token received.")
    
    # 2. Call Reset Endpoint
    reset_url = f"{BASE_URL}/api/maintenance/reset/"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print("Triggering System Reset...")
    response = requests.post(reset_url, headers=headers)
    
    if response.status_code == 200:
        print("Reset request successful (200 OK).")
        print(response.json())
    else:
        print(f"Reset request failed: {response.status_code} - {response.text}")
        sys.exit(1)
        
    # 3. Verify Re-Login
    print("Verifying admin access after reset...")
    time.sleep(2) # Wait a bit for DB effectively commit or whatever
    # New login attempt
    response = requests.post(login_url, json=credentials)
    
    if response.status_code == 200:
        print("SUCCESS: Admin access restored after reset!")
    else:
        print(f"FAILURE: Could not login after reset: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_reset()

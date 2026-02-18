import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIRequestFactory
from users.views import CustomTokenObtainPairView
from django.contrib.auth import get_user_model

def debug_login():
    print("=== DEBUG LOGIN (Token Obtain) ===")
    
    User = get_user_model()
    # Ensure admin exists
    if not User.objects.filter(username='admin').exists():
        print("User 'admin' does not exist!")
        return

    print("Attempting login for user 'admin'...")
    
    factory = APIRequestFactory()
    view = CustomTokenObtainPairView.as_view()
    
    # Mock POST request
    data = {
        'username': 'admin',
        'password': 'admin123' # Assuming default password
    }
    request = factory.post('/api/token/', data, format='json')
    
    try:
        response = view(request)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
             print("Login Successful!")
             print(response.data.keys())
        else:
             print("Login Failed!")
             print(response.data)
             
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Exception during login view:")
        print(e)
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_login()

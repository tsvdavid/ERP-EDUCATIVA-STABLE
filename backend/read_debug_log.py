try:
    with open('/tmp/login_debug.log', 'r') as f:
        print(f.read())
except FileNotFoundError:
    print("Debug log not found in /tmp")
except Exception as e:
    print(f"Error reading log: {e}")

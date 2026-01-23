import os
import psutil
import datetime

def check_python_processes():
    print("Checking Python processes...")
    current_pid = os.getpid()
    
    for proc in psutil.process_iter(['pid', 'name', 'create_time', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                create_time = datetime.datetime.fromtimestamp(proc.info['create_time'])
                uptime = datetime.datetime.now() - create_time
                cmd = " ".join(proc.info['cmdline'] or [])
                
                if 'manage.py' in cmd and 'runserver' in cmd:
                    print(f"FOUND SERVER: PID={proc.info['pid']}, Uptime={uptime}")
                    if uptime.total_seconds() > 3600:
                        print("CRITICAL: Server is running for more than 1 hour. CHANGES NOT APPLIED.")
                    else:
                        print("Server suggests recent restart.")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

if __name__ == "__main__":
    check_python_processes()

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User, Institution

print(f"Institutions count: {Institution.objects.count()}")
for inst in Institution.objects.all():
    print(f"Institution: {inst.name} (ID: {inst.id})")

print(f"Users count: {User.objects.count()}")
admin = User.objects.filter(username='admin').first()
if admin:
    print("Admin user found. Resetting password to 'admin123'.")
    admin.set_password('admin123')
    admin.save()
else:
    print("Admin user not found. Creating 'admin' with password 'admin123'.")
    # Need to check constraints. Assuming minimal fields.
    try:
        inst = Institution.objects.first()
        if not inst:
             inst = Institution.objects.create(name="Default Institution", email="admin@example.com")
        
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123', institution=inst)
        print("Admin user created.")
    except Exception as e:
        print(f"Error creating admin: {e}")


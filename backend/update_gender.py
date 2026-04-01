import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User

def infer_gender(first_name):
    name = first_name.strip().lower()
    if not name:
        return 'M' # Default
        
    # Nombres femeninos comunes que no terminan en 'a'
    female_exceptions = [
        'carmen', 'marisol', 'rut', 'isabel', 'beatriz', 'inés', 
        'luz', 'paz', 'mercedes', 'dolores', 'pilar', 'rosario', 'consuelo', 'abigail', 'raquel', 'ester', 'lizeth', 'mabel', 'miriam'
    ]
    # Nombres masculinos que sí terminan en 'a'
    male_exceptions = [
        'jose', 'andrea' # (en italia es M, pero en latinoamerica es F, ignoremos),
        'luca', 'bautista', 'josué'
    ]

    parts = name.split()
    first_word = parts[0] if parts else ''

    if first_word in male_exceptions:
        return 'M'
    if first_word in female_exceptions or first_word.endswith('a'):
        return 'F'
    
    return 'M'

def main():
    users = User.objects.all()
    count_m = 0
    count_f = 0
    
    for user in users:
        new_gender = infer_gender(user.first_name)
        user.gender = new_gender
        user.save(update_fields=['gender'])
        if new_gender == 'M':
            count_m += 1
        else:
            count_f += 1

    print(f"✅ Se actualizaron {users.count()} usuarios:")
    print(f"   - Hombres (M): {count_m}")
    print(f"   - Mujeres (F): {count_f}")

if __name__ == '__main__':
    main()

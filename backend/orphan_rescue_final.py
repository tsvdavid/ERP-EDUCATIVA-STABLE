import os
import django
import csv

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.apps import apps
from core.models import TenantModel
from users.models import Institution, User
from core.thread_context import set_current_tenant_id

def rescue():
    # Usar superusuario o bypass para esta operación
    audit_tenant = Institution.objects.get(id=9)
    csv_path = '/app/orphan_audit_report.csv'
    
    if not os.path.exists(csv_path):
        print("Error: No se encontró el reporte de auditoría.")
        return

    print("Iniciando Rescate de Huérfanos...")
    
    with open(csv_path, mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            model_name = row['modelo']
            obj_id = row['id']
            classification = row['clasificacion']
            
            try:
                # Buscar el modelo dinámicamente
                model = None
                for m in apps.get_models():
                    if m.__name__ == model_name and issubclass(m, TenantModel):
                        model = m
                        break
                
                if model:
                    # Desactivar filtrado de manager para encontrar el huérfano
                    # Usamos _base_manager o el manager por defecto sin filtro
                    # Como ya implementamos Active Manager, necesitamos bypass
                    set_current_tenant_id(None) # Superuser context o bypass
                    obj = model.objects.filter(id=obj_id, institution__isnull=True).first()
                    
                    if obj:
                        obj.institution = audit_tenant
                        obj.is_orphaned = True
                        obj.save()
                        print(f"Rescatado: {model_name} ID {obj_id} -> SYSTEM (Auditoría)")
                    else:
                        print(f"Omitido: {model_name} ID {obj_id} (Ya tiene institución o no existe)")
            except Exception as e:
                print(f"Error rescatando {model_name} ID {obj_id}: {e}")

if __name__ == "__main__":
    rescue()

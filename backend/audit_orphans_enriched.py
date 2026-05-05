import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.apps import apps
from core.models import TenantModel
from users.models import Institution
import csv

def audit():
    tenant_models = [m for m in apps.get_models() if issubclass(m, TenantModel)]
    report = []
    
    print("Iniciando Auditoría Enriquecida de Huérfanos...")
    
    for model in tenant_models:
        orphans = model.objects.filter(institution__isnull=True)
        count = orphans.count()
        if count == 0: continue
        
        print(f"Analizando {model.__name__} ({count} huérfanos)...")
        
        # Identificar relaciones para inferir contexto
        rel_fields = [f for f in model._meta.get_fields() if f.is_relation and not f.auto_created and f.name != 'institution']
        
        for obj in orphans:
            metadata = {}
            classification = "C (Corrupto/Sin relación)"
            recovered_inst = None
            
            for rf in rel_fields:
                try:
                    rel_obj = getattr(obj, rf.name)
                    if rel_obj:
                        inst_id = getattr(rel_obj, 'institution_id', None)
                        metadata[rf.name] = f"ID:{rel_obj.id}|Inst:{inst_id}"
                        if inst_id and not recovered_inst:
                            recovered_inst = inst_id
                            classification = "A (Recuperable)"
                        elif inst_id and recovered_inst and inst_id != recovered_inst:
                            classification = "B (Inconsistente/Conflictivo)"
                except: pass
            
            report.append({
                'modelo': model.__name__,
                'id': obj.id,
                'clasificacion': classification,
                'inst_sugerida': recovered_inst,
                'contexto': str(metadata),
                'created_at': getattr(obj, 'created_at', 'N/A')
            })

    # Guardar Reporte CSV
    keys = report[0].keys() if report else []
    with open('/var/www/erpeducativa/ERP-EDUCATIVA/backend/orphan_audit_report.csv', 'w', newline='') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(report)
    
    print(f"\nAuditoría completa. {len(report)} registros procesados.")
    print("Reporte guardado en: /app/orphan_audit_report.csv")

if __name__ == "__main__":
    audit()

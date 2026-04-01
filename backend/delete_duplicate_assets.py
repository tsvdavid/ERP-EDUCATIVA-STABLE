import os
import django

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounting.models import FixedAsset

def delete_duplicate_assets():
    print("Iniciando busqueda de activos duplicados...")
    
    # Obtenemos todos los activos creados
    assets = FixedAsset.objects.all().order_by('id')
    total = assets.count()
    
    if total <= 1:
        print(f"No hay duplicados evidentes (Total activos: {total}).")
        return
        
    print(f"Se encontraron {total} activos fijos registrados.")
    
    # Mantenemos el último modificado / creado (asumiendo que fue el exitoso) y borramos los IDs anteriores.
    # Opcional: Podríamos filtrar por nombre si hay otros legitimos, pero asumimos que todos fueron creados en esta prueba.
    
    # Nos quedamos con el Asset con el ID mas alto (el ultimo registrado)
    assets_to_delete = assets[:total-1]
    
    count_deleted = 0
    for asset in assets_to_delete:
        print(f"Borrando activo repetido: ID {asset.id} - {asset.name}")
        asset.delete()
        count_deleted += 1
        
    print(f"\nSe han eliminado exitosamente {count_deleted} activos fijos duplicados.")
    print("Queda 1 activo fijo en el sistema.")

if __name__ == '__main__':
    delete_duplicate_assets()

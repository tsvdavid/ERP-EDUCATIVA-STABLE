'''init_modules.py'''
"""Bootstrap script for ERP‑EDUCATIVA

Purpose
-------
- Create the minimal set of *Module* records required by the frontend menu.
- Associate those modules with the **active** Subscription (status = 'ACTIVE').
- The script is **idempotent** – running it repeatedly will never create duplicate rows.
- No data is deleted, migrations are untouched, and existing institutions/subscriptions are preserved.

How to run
----------
Inside the project root (where *docker‑compose.dev.yml* lives):

```bash
docker compose -f docker-compose.dev.yml exec -T backend python /app/init_modules.py
```

(Replace ``/app`` with the correct container working directory if it differs.)
"""

import os
import sys

# ---------------------------------------------------------------------------
# Django bootstrap
# ---------------------------------------------------------------------------
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django

django.setup()

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
from subscriptions.models import Module, Subscription, SubscriptionModule
from django.db import transaction

# ---------------------------------------------------------------------------
# Configuration – list of base modules (code must be unique)
# ---------------------------------------------------------------------------
BASE_MODULES = [
    {"code": "users", "name": "Usuarios"},
    {"code": "academic", "name": "Académico"},
    {"code": "treasury", "name": "Tesorería"},
    {"code": "accounting", "name": "Contabilidad"},
    {"code": "learning", "name": "Aprendizaje"},
    {"code": "communication", "name": "Comunicación"},
    {"code": "subscriptions", "name": "Suscripciones"},
]


def create_modules():
    """Create missing Module objects.

    Uses ``get_or_create`` so the operation is safe to repeat.
    Returns a list with the created or existing Module instances.
    """
    modules = []
    for data in BASE_MODULES:
        obj, created = Module.objects.get_or_create(code=data["code"], defaults={"name": data["name"]})
        if created:
            print(f"[+] Created Module: {obj.code} – {obj.name}")
        else:
            # Ensure name is up‑to‑date in case the code existed with a different name.
            if obj.name != data["name"]:
                obj.name = data["name"]
                obj.save(update_fields=["name"])
                print(f"[~] Updated name for Module {obj.code} to '{obj.name}'")
        modules.append(obj)
    return modules


def link_modules_to_subscription(modules):
    """Link each module to the *active* subscription.

    The system defines a one‑to‑many relationship via ``SubscriptionModule``.
    The function is also idempotent – ``get_or_create`` guarantees no duplicates.
    """
    # Find the subscription that is ACTIVE. There should be exactly one per institution.
    subscription = Subscription.objects.filter(status="ACTIVE").first()
    if not subscription:
        print("[!] No active Subscription found – skipping linking step.")
        return

    print(f"[i] Active subscription: {subscription.id} (institution: {subscription.institution})")

    for module in modules:
        obj, created = SubscriptionModule.objects.get_or_create(
            subscription=subscription, module=module
        )
        if created:
            print(f"[+] Linked Module '{module.code}' to Subscription {subscription.id}")
        else:
            # Already linked – nothing to do.
            pass


def main():
    print("--- ERP‑EDUCATIVA Module bootstrap start ---")
    with transaction.atomic():
        modules = create_modules()
        link_modules_to_subscription(modules)
    # Summary
    total_modules = Module.objects.count()
    total_links = SubscriptionModule.objects.count()
    print(f"[✓] Total Module records: {total_modules}")
    print(f"[✓] Total Subscription‑Module links: {total_links}")
    print("--- bootstrap completed ---")

if __name__ == "__main__":
    main()

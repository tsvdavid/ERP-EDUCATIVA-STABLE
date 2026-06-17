# -*- coding: utf-8 -*-
"""Management command to complete minimal bootstrap.

This command implements the missing stage after READY_MINIMAL:
    READY_MINIMAL -> CREATE_GLOBAL_SUPERUSER -> wizard_completed=True -> setup_status='READY_FULL'
It is deliberately minimal, idempotent and performs no side‑effects beyond the
required state transitions.
"""

import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from django.contrib.auth import get_user_model
from users.models import Institution


class Command(BaseCommand):
    help = "Complete the minimal bootstrap by ensuring a global superuser exists and marks the system as READY_FULL"

    def add_arguments(self, parser):
        # No arguments required; all configuration via env vars.
        pass

    def handle(self, *args, **options):
        # Environment variables for bootstrap superuser (used in development only).
        USERNAME = os.getenv("BOOTSTRAP_SUPERUSER_USERNAME", "admin")
        EMAIL = os.getenv("BOOTSTRAP_SUPERUSER_EMAIL", "admin@example.com")
        PASSWORD = os.getenv("BOOTSTRAP_SUPERUSER_PASSWORD")

        # Step 1 – Verify exactly one Institution exists.
        institution_qs = Institution.objects.all()
        count = institution_qs.count()
        if count == 0:
            raise CommandError("No Institution found. Exactly one Institution must exist to run this command.")
        if count > 1:
            raise CommandError(f"Multiple ({count}) Institutions found. This command expects a single Institution.")
        institution = institution_qs.first()

        User = get_user_model()

        # Step 2 – Ensure a global superuser exists.
        superuser_qs = User.objects.filter(is_superuser=True)
        if superuser_qs.exists():
            self.stdout.write(self.style.SUCCESS("Global superuser already exists – no changes made."))
        else:
            # In DEBUG mode we can fall back to defaults, otherwise password is mandatory.
            if not settings.DEBUG and not PASSWORD:
                raise CommandError(
                    "BOOTSTRAP_SUPERUSER_PASSWORD environment variable is required in production (DEBUG=False)."
                )
            # Use provided/ default values.
            password = PASSWORD or "admin123"
            superuser = User.objects.create_superuser(
                username=USERNAME,
                email=EMAIL,
                password=password,
                # Global superuser is not bound to any institution.
                institution=None,
                role=User.Role.GLOBAL,
            )
            self.stdout.write(self.style.SUCCESS(f"Created global superuser: {superuser.username}"))

        # Step 3 – Update wizard_completed and setup_status if needed.
        updates = []
        if not institution.wizard_completed:
            institution.wizard_completed = True
            updates.append("wizard_completed")
        if institution.setup_status != "READY_FULL":
            institution.setup_status = "READY_FULL"
            updates.append("setup_status")

        # Step 4 – Wrap everything in an atomic transaction.
        try:
            with transaction.atomic():
                # The superuser creation already happened outside the block; we only need to
                # persist the Institution changes if any.
                if updates:
                    institution.save(update_fields=updates)
                    self.stdout.write(self.style.SUCCESS(f"Institution updated fields: {', '.join(updates)}"))
                else:
                    self.stdout.write(self.style.SUCCESS("Institution already in READY_FULL state – no updates needed."))
        except Exception as exc:
            raise CommandError(f"Bootstrap command failed: {exc}")

import os
import django
import sys
import json

sys.path.append("/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from treasury.serializers import CreateInvoiceSerializer

payload = {
    "student_id": 2,
    "payment_method_id": None,
    "client_name": "Test",
    "client_ruc": "9999999999",
    "client_address": "Test",
    "client_email": "test@test.com",
    "concepts": [{"concept_id": 1, "quantity": 1}]
}

serializer = CreateInvoiceSerializer(data=payload)
if not serializer.is_valid():
    print("ERRORS:", serializer.errors)
else:
    print("VALID:", serializer.validated_data)

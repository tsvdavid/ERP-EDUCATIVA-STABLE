# apps/data_engine/templates/tests/test_tarea28.py
"""Comprehensive unit, integration, and Zero-ORM verification suite for TAREA 28 Package Manager."""

import ast
from decimal import Decimal
import os
import tempfile
import zipfile
import unittest
from typing import Any, Dict, List

from apps.data_engine.templates import TemplateRegistry, TemplateVersion
from apps.data_engine.templates.standard import StudentEnrollmentTemplate
from apps.data_engine.templates.packaging import (
    PackageManager,
    TemplateMigrator,
    TemplatePackage,
    PackageMetadata,
    SignatureVerificationException,
    InvalidPackageException,
    MigrationException,
)


class TestPackageModelsAndSerialization(unittest.TestCase):
    """Verify package DTO metadata serialization."""

    def test_package_metadata_serialization(self):
        meta = PackageMetadata(
            name="student_import",
            version="1.0.0",
            created_at="2026-07-13T12:00:00",
            author="DevTeam",
            description="Student Enrollment Package",
            checksum="hash123",
            is_signed=True,
        )
        data = meta.to_dict()
        self.assertEqual(data["name"], "student_import")
        self.assertEqual(data["version"], "1.0.0")
        self.assertEqual(data["author"], "DevTeam")
        self.assertEqual(data["checksum"], "hash123")
        self.assertTrue(data["is_signed"])


class TestPackageManagerLifecycle(unittest.TestCase):
    """Verify pack, sign, unpack, signature validation, and deployment operations."""

    def setUp(self):
        self.key = b"super_secret_hmac_signing_key_12345"
        self.wrong_key = b"wrong_signing_key_9876543210"
        self.registry = TemplateRegistry.global_registry()
        self.pm = PackageManager(self.registry)
        self.template = StudentEnrollmentTemplate()

        # Create temporary path for package testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pkg_path = os.path.join(self.temp_dir.name, "test_template.macpkg")

    def tearDown(self):
        self.temp_dir.cleanup()
        try:
            self.registry.remove("student_enrollment")
        except Exception:
            pass

    def test_pack_and_unpack_cycle_success(self):
        # Pack
        self.pm.pack(
            template=self.template,
            key=self.key,
            output_path=self.pkg_path,
            author="TestingEngine",
            description="Dynamic Test Package",
        )
        self.assertTrue(os.path.exists(self.pkg_path))

        # Unpack
        package = self.pm.unpack(self.pkg_path, self.key)
        self.assertIsInstance(package, TemplatePackage)
        self.assertEqual(package.metadata.name, "student_enrollment")
        self.assertEqual(package.metadata.author, "TestingEngine")
        self.assertTrue(package.metadata.is_signed)
        self.assertEqual(package.template_definition.code, "student_enrollment")
        self.assertEqual(package.pipeline_definition.connector.connector_type, "csv")

    def test_unpack_with_incorrect_key_raises_signature_error(self):
        # Pack
        self.pm.pack(self.template, self.key, self.pkg_path)

        # Unpack with wrong key
        with self.assertRaises(SignatureVerificationException):
            self.pm.unpack(self.pkg_path, self.wrong_key)

    def test_unpack_tampered_package_raises_signature_error(self):
        # Pack
        self.pm.pack(self.template, self.key, self.pkg_path)

        # Corrupt package by rewriting metadata.json with fake data inside the zip
        corrupted_path = os.path.join(self.temp_dir.name, "corrupted_template.macpkg")
        
        with zipfile.ZipFile(self.pkg_path, "r") as orig_zip:
            with zipfile.ZipFile(corrupted_path, "w") as fake_zip:
                for file_info in orig_zip.infolist():
                    data = orig_zip.read(file_info.filename)
                    if file_info.filename == "metadata.json":
                        # Tamper!
                        data = b'{"name": "student_enrollment", "version": "9.9.9", "author": "Hacker"}'
                    fake_zip.writestr(file_info.filename, data)

        # Unpack corrupted package
        with self.assertRaises(SignatureVerificationException):
            self.pm.unpack(corrupted_path, self.key)

    def test_unpack_missing_manifest_raises_invalid_package(self):
        bad_path = os.path.join(self.temp_dir.name, "bad.macpkg")
        with zipfile.ZipFile(bad_path, "w") as bad_zip:
            bad_zip.writestr("schema.json", b"{}")

        with self.assertRaises(InvalidPackageException):
            self.pm.unpack(bad_path, self.key)

    def test_publish_and_unpublish_lifecycle(self):
        # Pack
        self.pm.pack(self.template, self.key, self.pkg_path)
        package = self.pm.unpack(self.pkg_path, self.key)

        # Publish
        dyn_tpl = self.pm.publish(package, set_active=True, overwrite=True)
        self.assertEqual(dyn_tpl.code, "student_enrollment")

        # Confirm registry loading
        resolved = self.registry.get("student_enrollment")
        self.assertEqual(resolved.name, "Plantilla Estándar de Matrícula de Estudiantes")
        self.assertEqual(str(resolved.version), "1.0.0")

        # Unpublish
        self.pm.unpublish("student_enrollment", "1.0.0")
        with self.assertRaises(Exception):
            self.registry.get("student_enrollment", "1.0.0")


class TestTemplateMigrator(unittest.TestCase):
    """Verify data transformation mapping rules and chain of version hop migrations."""

    def setUp(self):
        self.migrator = TemplateMigrator()

    def test_migrate_no_op_for_identical_versions(self):
        records = [{"id": 1, "val": "A"}]
        result = self.migrator.migrate("test_tpl", "1.0.0", "1.0.0", records)
        self.assertEqual(result, records)

    def test_declarative_migration_step(self):
        rules = {
            "deletions": ["deprecated_col"],
            "renames": {"monto": "monto_bruto"},
            "defaults": {"pais": "Ecuador"},
            "conversions": {
                "monto_bruto": "Decimal",
                "edad": "int",
                "nombre": "upper",
            },
        }
        self.migrator.register_migration("finance_tpl", "1.0.0", "2.0.0", rules)

        records = [
            {
                "deprecated_col": "drop_me",
                "monto": "150.50",
                "edad": "25",
                "nombre": "  juan perez  ",
            }
        ]

        migrated = self.migrator.migrate("finance_tpl", "1.0.0", "2.0.0", records)
        self.assertEqual(len(migrated), 1)
        rec = migrated[0]

        self.assertNotIn("deprecated_col", rec)
        self.assertEqual(rec["monto_bruto"], Decimal("150.50"))
        self.assertEqual(rec["edad"], 25)
        self.assertEqual(rec["nombre"], "  JUAN PEREZ  ")
        self.assertEqual(rec["pais"], "Ecuador")

    def test_chained_multi_hop_migration(self):
        # 1.0.0 -> 1.1.0 (Rename)
        self.migrator.register_migration(
            "student_tpl", "1.0.0", "1.1.0", {"renames": {"email": "correo"}}
        )
        # 1.1.0 -> 2.0.0 (Conversion and Default)
        self.migrator.register_migration(
            "student_tpl",
            "1.1.0",
            "2.0.0",
            {
                "defaults": {"status": "active"},
                "conversions": {"correo": "lower"},
            },
        )

        records = [{"email": "JOHN@EDUKA360.COM"}]
        migrated = self.migrator.migrate("student_tpl", "1.0.0", "2.0.0", records)

        self.assertEqual(len(migrated), 1)
        rec = migrated[0]
        self.assertNotIn("email", rec)
        self.assertEqual(rec["correo"], "john@eduka360.com")
        self.assertEqual(rec["status"], "active")

    def test_custom_callable_migration(self):
        def custom_fn(rec: Dict[str, Any]) -> Dict[str, Any]:
            res = dict(rec)
            res["computed_val"] = int(rec["val"]) * 2
            return res

        self.migrator.register_migration("custom_tpl", "1.0.0", "2.0.0", custom_fn)
        records = [{"val": "10"}]
        migrated = self.migrator.migrate("custom_tpl", "1.0.0", "2.0.0", records)
        self.assertEqual(migrated[0]["computed_val"], 20)

    def test_unresolved_migration_path_raises(self):
        with self.assertRaises(MigrationException):
            self.migrator.migrate("missing_tpl", "1.0.0", "2.0.0", [{"a": 1}])


class TestZeroOrmComplianceInPackaging(unittest.TestCase):
    """Ensure no database dependency is imported or utilized in the packaging layer."""

    def test_packaging_package_has_no_django_orm_dependencies(self):
        forbidden_modules = {"django.db", "django.db.models", "django.db.transaction"}
        forbidden_names = {"models", "QuerySet", "atomic"}

        package_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "packaging")
        )

        for root, _, files in os.walk(package_dir):
            for file in files:
                if not file.endswith(".py"):
                    continue
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=filepath)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            for forbidden in forbidden_modules:
                                self.assertFalse(
                                    alias.name == forbidden or alias.name.startswith(f"{forbidden}."),
                                    f"Zero-ORM violation in {filepath}: import {alias.name}",
                                )
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            for forbidden in forbidden_modules:
                                self.assertFalse(
                                    node.module == forbidden or node.module.startswith(f"{forbidden}."),
                                    f"Zero-ORM violation in {filepath}: from {node.module} import ...",
                                )
                    elif isinstance(node, ast.Name):
                        if node.id in forbidden_names:
                            self.assertNotEqual(
                                node.id,
                                "QuerySet",
                                f"Zero-ORM violation in {filepath}: direct use of {node.id}",
                            )

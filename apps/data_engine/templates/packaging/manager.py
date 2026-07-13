# apps/data_engine/templates/packaging/manager.py
"""Central package manager responsible for packaging, verifying, signing, and deploying .macpkg bundles."""

import datetime
import hashlib
import hmac
import json
import os
from typing import Any, Dict, Optional
import zipfile

from apps.data_engine.templates.base import BaseImportTemplate
from apps.data_engine.templates.models import (
    ColumnDefinition,
    ConnectorDefinition,
    ImportPipelineDefinition,
    LoaderDefinition,
    TemplateDefinition,
    TemplateVersion,
    TransformationDefinition,
    ValidatorDefinition,
)
from apps.data_engine.templates.registry import TemplateRegistry
from apps.data_engine.templates.packaging.models import PackageMetadata, TemplatePackage
from apps.data_engine.templates.packaging.exceptions import (
    InvalidPackageException,
    PackageException,
    SignatureVerificationException,
)
from apps.data_engine.templates.packaging.dynamic import DynamicImportTemplate


class PackageManager:
    """Enterprise Package Manager orchestrating the lifecycle and deployment of signed import templates."""

    def __init__(self, registry: Optional[TemplateRegistry] = None) -> None:
        self.registry = registry or TemplateRegistry.global_registry()

    def pack(
        self,
        template: BaseImportTemplate,
        key: bytes,
        output_path: str,
        author: str = "System",
        description: str = "",
        migration_rules: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Serialize an import template configuration, sign it with HMAC-SHA256, and write a ZIP-compressed .macpkg."""
        if not template:
            raise ValueError("Template cannot be None.")
        if not key:
            raise ValueError("Signing key cannot be empty.")
        if not output_path:
            raise ValueError("Output path cannot be empty.")

        tdef = template.get_template_definition()
        pdef = template.get_pipeline_definition()
        rules = migration_rules or {}

        schema_dict = tdef.to_dict()
        pipeline_dict = pdef.to_dict()

        # Deterministic serialization for hashing and signing
        schema_bytes = json.dumps(schema_dict, sort_keys=True, ensure_ascii=True).encode("utf-8")
        pipeline_bytes = json.dumps(pipeline_dict, sort_keys=True, ensure_ascii=True).encode("utf-8")
        migration_bytes = json.dumps(rules, sort_keys=True, ensure_ascii=True).encode("utf-8")

        # 1. Calculate integrity SHA256 checksum
        hasher = hashlib.sha256()
        hasher.update(schema_bytes)
        hasher.update(pipeline_bytes)
        hasher.update(migration_bytes)
        checksum = hasher.hexdigest()

        # 2. Build metadata
        meta = PackageMetadata(
            name=template.code,
            version=str(template.version),
            created_at=datetime.datetime.now().isoformat()[:19],
            author=author,
            description=description or template.name,
            checksum=checksum,
            is_signed=True,
        )
        meta_dict = meta.to_dict()
        meta_bytes = json.dumps(meta_dict, sort_keys=True, ensure_ascii=True).encode("utf-8")

        # 3. Cryptographically sign the concatenated package bytes
        signer = hmac.new(key, digestmod=hashlib.sha256)
        signer.update(meta_bytes)
        signer.update(schema_bytes)
        signer.update(pipeline_bytes)
        signer.update(migration_bytes)
        signature = signer.hexdigest()

        # 4. Save components inside target compressed ZIP archive
        try:
            # Ensure parent directories exist
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_ref:
                zip_ref.writestr("metadata.json", meta_bytes)
                zip_ref.writestr("schema.json", schema_bytes)
                zip_ref.writestr("pipeline.json", pipeline_bytes)
                zip_ref.writestr("migration.json", migration_bytes)
                zip_ref.writestr("signature.sha256", signature.encode("utf-8"))
        except Exception as exc:
            raise PackageException(f"Failed to generate package at '{output_path}': {exc}") from exc

    def unpack(self, package_path: str, key: bytes) -> TemplatePackage:
        """Load, authenticate, and unpack a template package archive, returning a TemplatePackage DTO."""
        if not package_path or not os.path.exists(package_path):
            raise InvalidPackageException(f"Package file not found at '{package_path}'.")
        if not key:
            raise ValueError("Verification key cannot be empty.")

        try:
            with zipfile.ZipFile(package_path, "r") as zip_ref:
                namelist = zip_ref.namelist()
                for req in ["metadata.json", "schema.json", "pipeline.json", "signature.sha256"]:
                    if req not in namelist:
                        raise InvalidPackageException(f"Corrupt package file: missing required element '{req}'.")

                meta_bytes = zip_ref.read("metadata.json")
                schema_bytes = zip_ref.read("schema.json")
                pipeline_bytes = zip_ref.read("pipeline.json")
                migration_bytes = zip_ref.read("migration.json") if "migration.json" in namelist else b"{}"
                signature_saved = zip_ref.read("signature.sha256").decode("utf-8").strip()
        except InvalidPackageException:
            raise
        except zipfile.BadZipFile as exc:
            raise InvalidPackageException(f"File is not a valid zip archive: {exc}") from exc
        except Exception as exc:
            raise PackageException(f"Failed reading package archive: {exc}") from exc

        # 1. Cryptographic Signature Verification
        signer = hmac.new(key, digestmod=hashlib.sha256)
        signer.update(meta_bytes)
        signer.update(schema_bytes)
        signer.update(pipeline_bytes)
        signer.update(migration_bytes)
        signature_calc = signer.hexdigest()

        if not hmac.compare_digest(signature_saved, signature_calc):
            raise SignatureVerificationException("Package integrity verification failed: invalid signature.")

        # 2. Parse DTO Components
        try:
            meta_dict = json.loads(meta_bytes)
            schema_dict = json.loads(schema_bytes)
            pipeline_dict = json.loads(pipeline_bytes)
            migration_rules = json.loads(migration_bytes)
        except json.JSONDecodeError as exc:
            raise InvalidPackageException(f"JSON syntax error parsing package elements: {exc}")

        try:
            # Hydrate Metadata DTO
            meta = PackageMetadata(
                name=meta_dict["name"],
                version=meta_dict["version"],
                created_at=meta_dict["created_at"],
                author=meta_dict["author"],
                description=meta_dict["description"],
                checksum=meta_dict.get("checksum", ""),
                is_signed=True,
            )

            # Hydrate TemplateDefinition DTO
            ver_status = schema_dict.get("version_status", "ACTIVE")
            version = TemplateVersion.parse(schema_dict["version"], status=ver_status)
            columns = [
                ColumnDefinition(
                    name=col["name"],
                    source_field=col["source_field"],
                    data_type=col.get("data_type", "str"),
                    required=col.get("required", False),
                    default_value=col.get("default_value"),
                    description=col.get("description", ""),
                )
                for col in schema_dict.get("columns", [])
            ]
            tdef = TemplateDefinition(
                code=schema_dict["code"],
                name=schema_dict["name"],
                version=version,
                columns=columns,
                target_entity=schema_dict.get("target_entity", ""),
                metadata=schema_dict.get("metadata", {}),
            )

            # Hydrate ImportPipelineDefinition DTO
            conn_dict = pipeline_dict["connector"]
            connector = ConnectorDefinition(
                connector_type=conn_dict["connector_type"],
                parameters=conn_dict.get("parameters", {}),
            )
            transformations = [
                TransformationDefinition(
                    transformation_type=tx["transformation_type"],
                    parameters=tx.get("parameters", {}),
                )
                for tx in pipeline_dict.get("transformations", [])
            ]
            validators = [
                ValidatorDefinition(
                    validator_type=v["validator_type"],
                    parameters=v.get("parameters", {}),
                )
                for v in pipeline_dict.get("validators", [])
            ]
            ldr_dict = pipeline_dict.get("loader", {})
            loader = LoaderDefinition(
                loader_type=ldr_dict.get("loader_type", "default"),
                target_table=ldr_dict.get("target_table", ""),
                batch_size=ldr_dict.get("batch_size", 1000),
                parameters=ldr_dict.get("parameters", {}),
            )
            pdef = ImportPipelineDefinition(
                connector=connector,
                mapping=pipeline_dict.get("mapping", {}),
                transformations=transformations,
                validators=validators,
                loader=loader,
                options=pipeline_dict.get("options", {}),
            )

            return TemplatePackage(
                metadata=meta,
                template_definition=tdef,
                pipeline_definition=pdef,
                migration_rules=migration_rules,
            )
        except (KeyError, ValueError, TypeError) as exc:
            raise InvalidPackageException(f"Structural integrity mismatch in package schema: {exc}")

    def publish(self, package: TemplatePackage, set_active: bool = True, overwrite: bool = True) -> BaseImportTemplate:
        """Instantiate a dynamic template from an authenticated package and register it into the TemplateRegistry."""
        if not package:
            raise ValueError("Package cannot be None.")

        # Build dynamic import template
        tpl = DynamicImportTemplate(
            template_definition=package.template_definition,
            pipeline_definition=package.pipeline_definition,
        )

        # Register template version
        self.registry.register(tpl, set_active=set_active, overwrite=overwrite)
        return tpl

    def unpublish(self, code: str, version: Optional[str] = None) -> None:
        """Remove a template or a specific version of a template from the TemplateRegistry."""
        self.registry.remove(code, version)

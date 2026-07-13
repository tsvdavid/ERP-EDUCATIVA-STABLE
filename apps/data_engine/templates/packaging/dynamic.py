# apps/data_engine/templates/packaging/dynamic.py
"""Dynamic template implementation allowing hot-reloading from serialized package schemas."""

from typing import List
from apps.data_engine.templates.base import BaseImportTemplate
from apps.data_engine.templates.models import (
    TemplateDefinition,
    ImportPipelineDefinition,
    TemplateVersion,
    TemplateValidationError,
)


class DynamicImportTemplate(BaseImportTemplate):
    """Import template dynamically hydrated from a validated declarative package schema."""

    def __init__(
        self,
        template_definition: TemplateDefinition,
        pipeline_definition: ImportPipelineDefinition,
    ) -> None:
        super().__init__()
        self._template_definition = template_definition
        self._pipeline_definition = pipeline_definition

    @property
    def code(self) -> str:
        return self._template_definition.code

    @property
    def name(self) -> str:
        return self._template_definition.name

    @property
    def version(self) -> TemplateVersion:
        return self._template_definition.version

    def get_template_definition(self) -> TemplateDefinition:
        return self._template_definition

    def get_pipeline_definition(self) -> ImportPipelineDefinition:
        return self._pipeline_definition

    def validate_template(self) -> List[TemplateValidationError]:
        errors: List[TemplateValidationError] = []
        if not self._template_definition.columns:
            errors.append(
                TemplateValidationError(
                    code="EMPTY_SCHEMA",
                    message="Template definition contains no columns.",
                    template_code=self.code,
                )
            )
        # Check mapping matches declared columns
        mapping = self._pipeline_definition.mapping
        declared_raw_fields = {col.raw_name for col in self._template_definition.columns}
        for raw_field in mapping.keys():
            if raw_field not in declared_raw_fields:
                errors.append(
                    TemplateValidationError(
                        code="UNRESOLVED_MAPPING_FIELD",
                        message=f"Mapped source field '{raw_field}' is not defined in column schema.",
                        template_code=self.code,
                        field=raw_field,
                    )
                )
        return errors

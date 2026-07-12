# apps/data_engine/templates/standard.py
"""Standard prebuilt enterprise import templates for the Eduka360 ERP."""

from typing import List

from .base import BaseImportTemplate
from .models import (
    ColumnDefinition,
    ConnectorDefinition,
    ImportPipelineDefinition,
    LoaderDefinition,
    TemplateDefinition,
    TemplateValidationError,
    TemplateVersion,
    TransformationDefinition,
    ValidatorDefinition,
)
from .registry import TemplateRegistry


class StudentEnrollmentTemplate(BaseImportTemplate):
    """Enterprise template for importing and validating student enrollments."""

    @property
    def code(self) -> str:
        return "student_enrollment"

    @property
    def name(self) -> str:
        return "Plantilla Estándar de Matrícula de Estudiantes"

    @property
    def version(self) -> TemplateVersion:
        return TemplateVersion(
            major=1,
            minor=0,
            patch=0,
            status="ACTIVE",
            changelog="Initial release of student enrollment template.",
        )

    def get_template_definition(self) -> TemplateDefinition:
        columns = [
            ColumnDefinition("student_id", "id_estudiante", "int", required=True, description="Identificador único del estudiante"),
            ColumnDefinition("full_name", "nombre_completo", "str", required=True, description="Nombre completo del estudiante"),
            ColumnDefinition("email", "correo", "str", required=False, description="Correo electrónico institucional o personal"),
            ColumnDefinition("enrolled_date", "fecha_matricula", "date", required=False, description="Fecha formal de matrícula"),
        ]
        return TemplateDefinition(
            code=self.code,
            name=self.name,
            version=self.version,
            columns=columns,
            target_entity="Student",
            metadata={"category": "Academic", "author": "Eduka360 Core Team"},
        )

    def get_pipeline_definition(self) -> ImportPipelineDefinition:
        return ImportPipelineDefinition(
            connector=ConnectorDefinition("csv", {"delimiter": ",", "encoding": "utf-8"}),
            mapping={
                "id_estudiante": "student_id",
                "nombre_completo": "full_name",
                "correo": "email",
                "fecha_matricula": "enrolled_date",
            },
            validators=[
                ValidatorDefinition("required_validator", {"fields": ["id_estudiante", "nombre_completo"]}),
                ValidatorDefinition("unique_validator", {"field": "id_estudiante"}),
                ValidatorDefinition("regex_validator", {"field": "correo", "pattern": r"^[\w\.\-]+@[\w\-]+\.[a-zA-Z]{2,}$"}),
            ],
            transformations=[
                TransformationDefinition("trim", {"fields": ["nombre_completo", "correo"]}),
                TransformationDefinition("rename_fields", {
                    "mapping": {
                        "id_estudiante": "student_id",
                        "nombre_completo": "full_name",
                        "correo": "email",
                        "fecha_matricula": "enrolled_date",
                    }
                }),
                TransformationDefinition("type_cast", {"type_mapping": {"student_id": "int", "enrolled_date": "date"}}),
            ],
            loader=LoaderDefinition("default", target_table="students_student", batch_size=500),
            options={"skip_header": True, "stop_on_first_error": False},
        )

    def validate_template(self) -> List[TemplateValidationError]:
        errors: List[TemplateValidationError] = []
        definition = self.get_template_definition()
        if not definition.columns:
            errors.append(
                TemplateValidationError(
                    code="EMPTY_COLUMNS",
                    message="Template must specify at least one column definition.",
                    template_code=self.code,
                )
            )
        return errors


class FinancialFeeTemplate(BaseImportTemplate):
    """Enterprise template for importing and validating financial fees and billing records."""

    @property
    def code(self) -> str:
        return "financial_fee"

    @property
    def name(self) -> str:
        return "Plantilla de Cobros y Cuotas Financieras"

    @property
    def version(self) -> TemplateVersion:
        return TemplateVersion(
            major=1,
            minor=0,
            patch=0,
            status="ACTIVE",
            changelog="Initial release of financial fees import template.",
        )

    def get_template_definition(self) -> TemplateDefinition:
        columns = [
            ColumnDefinition("fee_id", "id_cuota", "int", required=True, description="ID único del cobro o cuota"),
            ColumnDefinition("student_id", "id_estudiante", "int", required=True, description="ID del estudiante asociado"),
            ColumnDefinition("amount", "monto", "Decimal", required=True, description="Valor monetario del cobro"),
            ColumnDefinition("concept", "concepto", "str", required=False, description="Concepto o descripción del cobro"),
        ]
        return TemplateDefinition(
            code=self.code,
            name=self.name,
            version=self.version,
            columns=columns,
            target_entity="Fee",
            metadata={"category": "Financial", "author": "Eduka360 Core Team"},
        )

    def get_pipeline_definition(self) -> ImportPipelineDefinition:
        return ImportPipelineDefinition(
            connector=ConnectorDefinition("csv", {"delimiter": ",", "encoding": "utf-8"}),
            mapping={
                "id_cuota": "fee_id",
                "id_estudiante": "student_id",
                "monto": "amount",
                "concepto": "concept",
            },
            validators=[
                ValidatorDefinition("required_validator", {"fields": ["id_cuota", "id_estudiante", "monto"]}),
                ValidatorDefinition("range_validator", {"field": "monto", "min_val": 0}),
            ],
            transformations=[
                TransformationDefinition("trim", {"fields": ["concepto"]}),
                TransformationDefinition("rename_fields", {
                    "mapping": {
                        "id_cuota": "fee_id",
                        "id_estudiante": "student_id",
                        "monto": "amount",
                        "concepto": "concept",
                    }
                }),
                TransformationDefinition("type_cast", {"type_mapping": {"fee_id": "int", "student_id": "int", "amount": "Decimal"}}),
                TransformationDefinition("uppercase", {"fields": ["concept"]}),
            ],
            loader=LoaderDefinition("default", target_table="payments_fee", batch_size=1000),
            options={"skip_header": True, "stop_on_first_error": False},
        )

    def validate_template(self) -> List[TemplateValidationError]:
        errors: List[TemplateValidationError] = []
        definition = self.get_template_definition()
        if not definition.columns:
            errors.append(
                TemplateValidationError(
                    code="EMPTY_COLUMNS",
                    message="Template must specify at least one column definition.",
                    template_code=self.code,
                )
            )
        return errors


# Auto-register standard corporate templates into global registry
TemplateRegistry.global_registry().register(StudentEnrollmentTemplate(), set_active=True, overwrite=True)
TemplateRegistry.global_registry().register(FinancialFeeTemplate(), set_active=True, overwrite=True)

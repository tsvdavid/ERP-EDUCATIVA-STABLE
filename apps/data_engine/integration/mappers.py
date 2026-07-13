# apps/data_engine/integration/mappers.py
"""Entity mappers for translating DTOs / dictionary records to target ERP models."""

from typing import Any, Dict, List, Optional
from .contracts import BaseEntityMapper
from .dto import EntityMapping


class BaseMapper(BaseEntityMapper):
    """Generic mapper engine based on declarative field mappings."""

    def __init__(self, mappings: List[EntityMapping]):
        self.mappings = mappings

    def map_record(self, record: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        result = {}
        for mapping in self.mappings:
            val = record.get(mapping.source_field)
            if val is None:
                val = mapping.default_value

            if mapping.converter_name and val is not None:
                val = self.apply_conversion(val, mapping.converter_name)

            result[mapping.target_field] = val
        return result

    def apply_conversion(self, val: Any, converter_name: str) -> Any:
        """Converts type using specified converter name."""
        if converter_name == "int":
            try:
                return int(val)
            except (ValueError, TypeError):
                return 0
        elif converter_name == "float":
            try:
                return float(val)
            except (ValueError, TypeError):
                return 0.0
        elif converter_name == "str":
            return str(val).strip()
        elif converter_name == "upper":
            return str(val).strip().upper()
        elif converter_name == "lower":
            return str(val).strip().lower()
        elif converter_name == "bool":
            if isinstance(val, str):
                return val.strip().lower() in ("true", "1", "yes", "si")
            return bool(val)
        return val


class StudentMapper(BaseMapper):
    """Maps student data."""

    def __init__(self) -> None:
        super().__init__([
            EntityMapping("cedula", "identification", converter_name="str"),
            EntityMapping("nombres", "first_name", converter_name="upper"),
            EntityMapping("apellidos", "last_name", converter_name="upper"),
            EntityMapping("email", "email", converter_name="lower"),
            EntityMapping("telefono", "phone", converter_name="str", default_value=""),
            EntityMapping("edad", "age", converter_name="int", default_value=0),
        ])


class TeacherMapper(BaseMapper):
    """Maps teacher data."""

    def __init__(self) -> None:
        super().__init__([
            EntityMapping("identificacion", "identification", converter_name="str"),
            EntityMapping("nombre_completo", "full_name", converter_name="upper"),
            EntityMapping("correo", "email", converter_name="lower"),
            EntityMapping("especialidad", "specialty", converter_name="str", default_value="General"),
        ])


class RepresentativeMapper(BaseMapper):
    """Maps parent / representative data."""

    def __init__(self) -> None:
        super().__init__([
            EntityMapping("identificacion", "identification", converter_name="str"),
            EntityMapping("nombres", "first_name", converter_name="upper"),
            EntityMapping("apellidos", "last_name", converter_name="upper"),
            EntityMapping("parentesco", "relationship", converter_name="str", default_value="Padre"),
        ])


class FinancialMapper(BaseMapper):
    """Maps financial fee items."""

    def __init__(self) -> None:
        super().__init__([
            EntityMapping("codigo_rubro", "fee_code", converter_name="str"),
            EntityMapping("descripcion", "description", converter_name="str"),
            EntityMapping("valor", "amount", converter_name="float", default_value=0.0),
            EntityMapping("activo", "is_active", converter_name="bool", default_value=True),
        ])

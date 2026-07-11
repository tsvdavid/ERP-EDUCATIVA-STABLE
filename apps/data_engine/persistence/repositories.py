# apps/data_engine/persistence/repositories.py
"""Concrete multi-tenant repositories for the Transactional Persistence Adapter.

Encapsulates Django ORM queries (`models.py` imports) for entities:
- ``InstitutionRepository`` (`users.models.Institution`)
- ``AcademicPeriodRepository`` (`academic.models.AcademicPeriod`)
- ``CourseRepository`` (`academic.models.Course`)
- ``StudentRepository`` (`users.models.User` with role `STUDENT`)
- ``RepresentativeRepository`` (`users.models.User` with role `PARENT`)
- ``EnrollmentRepository`` (`academic.models.Enrollment`)
"""

from typing import Any, Dict, List, Optional
import time

from .base import BaseRepository
from .models import EntityPersistenceResult, PersistenceContext


def _get_duration_ms(start_time: float) -> float:
    return (time.perf_counter() - start_time) * 1000.0


def _extract_from_step_outputs(context: PersistenceContext, target_entity_name: str) -> Optional[str]:
    """Helper to extract an orm_id for a given entity_name from previous step outputs."""
    for out in context.resolved_dependencies.values():
        if isinstance(out, dict):
            ent_res = out.get("entity_result")
            if ent_res and getattr(ent_res, "entity_name", "") == target_entity_name and out.get("orm_id"):
                return out["orm_id"]
    return None


class InstitutionRepository(BaseRepository):
    """Repository managing `users.models.Institution` entities."""

    entity_name: str = "Institution"

    def _get_model(self):
        from users.models import Institution
        return Institution

    def resolve_dependencies(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> Dict[str, Any]:
        return {}

    def validate_constraints(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> List[str]:
        errors = []
        if not payload.get("name"):
            errors.append("Institution 'name' is required.")
        return errors

    def find_existing(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> Optional[Any]:
        Model = self._get_model()
        if "orm_id" in payload and payload["orm_id"]:
            return Model.objects.filter(pk=payload["orm_id"]).first()
        ruc = payload.get("ruc")
        if ruc:
            found = Model.objects.filter(ruc=ruc).first()
            if found:
                return found
        name = payload.get("name")
        if name:
            return Model.objects.filter(name=name).first()
        return None

    def create(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> EntityPersistenceResult:
        start = time.perf_counter()
        Model = self._get_model()
        fields = {k: v for k, v in payload.items() if hasattr(Model, k)}
        inst = Model.objects.create(**fields)
        return EntityPersistenceResult(
            node_id=payload.get("node_id", ""),
            entity_name=self.entity_name,
            orm_id=str(inst.pk),
            created=True,
            success=True,
            duration_ms=_get_duration_ms(start),
        )

    def update(
        self,
        existing_instance: Any,
        payload: Dict[str, Any],
        context: PersistenceContext,
    ) -> EntityPersistenceResult:
        start = time.perf_counter()
        for k, v in payload.items():
            if hasattr(existing_instance, k) and k not in ("id", "pk"):
                setattr(existing_instance, k, v)
        existing_instance.save()
        return EntityPersistenceResult(
            node_id=payload.get("node_id", ""),
            entity_name=self.entity_name,
            orm_id=str(existing_instance.pk),
            created=False,
            success=True,
            duration_ms=_get_duration_ms(start),
        )


class CourseRepository(BaseRepository):
    """Repository managing `academic.models.Course` entities."""

    entity_name: str = "Course"

    def _get_model(self):
        from academic.models import Course
        return Course

    def resolve_dependencies(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> Dict[str, Any]:
        resolved = {}
        if context.tenant_id and context.tenant_id != "default":
            from users.models import Institution
            inst = Institution.objects.filter(pk=context.tenant_id).first()
            if inst:
                resolved["institution"] = inst
        elif "institution_id" in context.resolved_dependencies:
            resolved["institution_id"] = context.resolved_dependencies["institution_id"]
        else:
            inst_id = _extract_from_step_outputs(context, "Institution")
            if inst_id:
                resolved["institution_id"] = inst_id
        return resolved

    def validate_constraints(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> List[str]:
        errors = []
        if not payload.get("name"):
            errors.append("Course 'name' is required.")
        if not payload.get("year"):
            errors.append("Course 'year' is required.")
        return errors

    def find_existing(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> Optional[Any]:
        Model = self._get_model()
        if "orm_id" in payload and payload["orm_id"]:
            return Model.objects.filter(pk=payload["orm_id"]).first()
        name = payload.get("name")
        year = payload.get("year", 2026)
        parallel = payload.get("parallel", "A")
        level = payload.get("level", "")
        qs = Model.objects.filter(name=name, year=year, parallel=parallel, level=level)
        if context.tenant_id and context.tenant_id != "default":
            qs = qs.filter(institution_id=context.tenant_id)
        return qs.first()

    def create(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> EntityPersistenceResult:
        start = time.perf_counter()
        Model = self._get_model()
        deps = self.resolve_dependencies(payload, context)
        fields = {k: v for k, v in payload.items() if hasattr(Model, k)}
        fields.update(deps)
        if "institution" not in fields and "institution_id" not in fields and context.tenant_id and context.tenant_id != "default":
            fields["institution_id"] = context.tenant_id
        course = Model.objects.create(**fields)
        return EntityPersistenceResult(
            node_id=payload.get("node_id", ""),
            entity_name=self.entity_name,
            orm_id=str(course.pk),
            created=True,
            success=True,
            duration_ms=_get_duration_ms(start),
        )

    def update(
        self,
        existing_instance: Any,
        payload: Dict[str, Any],
        context: PersistenceContext,
    ) -> EntityPersistenceResult:
        start = time.perf_counter()
        for k, v in payload.items():
            if hasattr(existing_instance, k) and k not in ("id", "pk", "institution"):
                setattr(existing_instance, k, v)
        existing_instance.save()
        return EntityPersistenceResult(
            node_id=payload.get("node_id", ""),
            entity_name=self.entity_name,
            orm_id=str(existing_instance.pk),
            created=False,
            success=True,
            duration_ms=_get_duration_ms(start),
        )


class StudentRepository(BaseRepository):
    """Repository managing `users.models.User` (`STUDENT`) entities."""

    entity_name: str = "Student"

    def _get_model(self):
        from users.models import User
        return User

    def resolve_dependencies(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> Dict[str, Any]:
        resolved = {}
        if context.tenant_id and context.tenant_id != "default":
            from users.models import Institution
            inst = Institution.objects.filter(pk=context.tenant_id).first()
            if inst:
                resolved["institution"] = inst
        else:
            inst_id = _extract_from_step_outputs(context, "Institution")
            if inst_id:
                resolved["institution_id"] = inst_id
        return resolved

    def validate_constraints(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> List[str]:
        errors = []
        if not payload.get("username") and not payload.get("cedula"):
            errors.append("Student requires either 'username' or 'cedula'.")
        return errors

    def find_existing(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> Optional[Any]:
        Model = self._get_model()
        if "orm_id" in payload and payload["orm_id"]:
            return Model.objects.filter(pk=payload["orm_id"], role="STUDENT").first()
        cedula = payload.get("cedula")
        qs = Model.objects.filter(role="STUDENT")
        if context.tenant_id and context.tenant_id != "default":
            qs = qs.filter(institution_id=context.tenant_id)
        if cedula:
            found = qs.filter(cedula=cedula).first()
            if found:
                return found
        username = payload.get("username")
        if username:
            return qs.filter(username=username).first()
        return None

    def create(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> EntityPersistenceResult:
        start = time.perf_counter()
        Model = self._get_model()
        deps = self.resolve_dependencies(payload, context)
        fields = {k: v for k, v in payload.items() if hasattr(Model, k)}
        fields.update(deps)
        fields["role"] = "STUDENT"
        if not fields.get("username"):
            fields["username"] = fields.get("cedula") or f"student_{time.time_ns()}"
        if "institution" not in fields and "institution_id" not in fields and context.tenant_id and context.tenant_id != "default":
            fields["institution_id"] = context.tenant_id
        student = Model.objects.create(**fields)
        return EntityPersistenceResult(
            node_id=payload.get("node_id", ""),
            entity_name=self.entity_name,
            orm_id=str(student.pk),
            created=True,
            success=True,
            duration_ms=_get_duration_ms(start),
        )

    def update(
        self,
        existing_instance: Any,
        payload: Dict[str, Any],
        context: PersistenceContext,
    ) -> EntityPersistenceResult:
        start = time.perf_counter()
        for k, v in payload.items():
            if hasattr(existing_instance, k) and k not in ("id", "pk", "role", "institution"):
                setattr(existing_instance, k, v)
        existing_instance.save()
        return EntityPersistenceResult(
            node_id=payload.get("node_id", ""),
            entity_name=self.entity_name,
            orm_id=str(existing_instance.pk),
            created=False,
            success=True,
            duration_ms=_get_duration_ms(start),
        )


class RepresentativeRepository(BaseRepository):
    """Repository managing `users.models.User` (`PARENT`) entities."""

    entity_name: str = "Representative"

    def _get_model(self):
        from users.models import User
        return User

    def resolve_dependencies(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> Dict[str, Any]:
        resolved = {}
        if context.tenant_id and context.tenant_id != "default":
            from users.models import Institution
            inst = Institution.objects.filter(pk=context.tenant_id).first()
            if inst:
                resolved["institution"] = inst
        else:
            inst_id = _extract_from_step_outputs(context, "Institution")
            if inst_id:
                resolved["institution_id"] = inst_id
        return resolved

    def validate_constraints(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> List[str]:
        errors = []
        if not payload.get("username") and not payload.get("cedula"):
            errors.append("Representative requires either 'username' or 'cedula'.")
        return errors

    def find_existing(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> Optional[Any]:
        Model = self._get_model()
        if "orm_id" in payload and payload["orm_id"]:
            return Model.objects.filter(pk=payload["orm_id"], role="PARENT").first()
        cedula = payload.get("cedula")
        qs = Model.objects.filter(role="PARENT")
        if context.tenant_id and context.tenant_id != "default":
            qs = qs.filter(institution_id=context.tenant_id)
        if cedula:
            found = qs.filter(cedula=cedula).first()
            if found:
                return found
        username = payload.get("username")
        if username:
            return qs.filter(username=username).first()
        return None

    def create(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> EntityPersistenceResult:
        start = time.perf_counter()
        Model = self._get_model()
        fields = {k: v for k, v in payload.items() if hasattr(Model, k)}
        fields["role"] = "PARENT"
        if not fields.get("username"):
            fields["username"] = fields.get("cedula") or f"parent_{time.time_ns()}"
        if "institution_id" not in fields and context.tenant_id and context.tenant_id != "default":
            fields["institution_id"] = context.tenant_id
        parent = Model.objects.create(**fields)
        return EntityPersistenceResult(
            node_id=payload.get("node_id", ""),
            entity_name=self.entity_name,
            orm_id=str(parent.pk),
            created=True,
            success=True,
            duration_ms=_get_duration_ms(start),
        )

    def update(
        self,
        existing_instance: Any,
        payload: Dict[str, Any],
        context: PersistenceContext,
    ) -> EntityPersistenceResult:
        start = time.perf_counter()
        for k, v in payload.items():
            if hasattr(existing_instance, k) and k not in ("id", "pk", "role", "institution"):
                setattr(existing_instance, k, v)
        existing_instance.save()
        return EntityPersistenceResult(
            node_id=payload.get("node_id", ""),
            entity_name=self.entity_name,
            orm_id=str(existing_instance.pk),
            created=False,
            success=True,
            duration_ms=_get_duration_ms(start),
        )


class AcademicPeriodRepository(BaseRepository):
    """Repository managing `academic.models.AcademicPeriod` entities."""

    entity_name: str = "AcademicPeriod"

    def _get_model(self):
        from academic.models import AcademicPeriod
        return AcademicPeriod

    def resolve_dependencies(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> Dict[str, Any]:
        resolved = {}
        if "academic_year" in context.resolved_dependencies:
            resolved["academic_year"] = context.resolved_dependencies["academic_year"]
        elif "academic_year_id" in context.resolved_dependencies:
            resolved["academic_year_id"] = context.resolved_dependencies["academic_year_id"]
        elif "academic_year_id" in payload:
            resolved["academic_year_id"] = payload["academic_year_id"]
        else:
            period_id = _extract_from_step_outputs(context, "AcademicPeriod")
            if period_id:
                resolved["academic_year_id"] = period_id
        if "institution" not in resolved and "institution_id" not in resolved:
            if context.tenant_id and context.tenant_id != "default":
                resolved["institution_id"] = context.tenant_id
            else:
                inst_id = _extract_from_step_outputs(context, "Institution")
                if inst_id:
                    resolved["institution_id"] = inst_id
        return resolved

    def validate_constraints(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> List[str]:
        errors = []
        if not payload.get("number"):
            errors.append("AcademicPeriod 'number' is required.")
        return errors

    def find_existing(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> Optional[Any]:
        Model = self._get_model()
        if "orm_id" in payload and payload["orm_id"]:
            return Model.objects.filter(pk=payload["orm_id"]).first()
        deps = self.resolve_dependencies(payload, context)
        number = payload.get("number")
        if "academic_year" in deps and number:
            return Model.objects.filter(academic_year=deps["academic_year"], number=number).first()
        if "academic_year_id" in deps and number:
            return Model.objects.filter(academic_year_id=deps["academic_year_id"], number=number).first()
        return None

    def create(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> EntityPersistenceResult:
        start = time.perf_counter()
        Model = self._get_model()
        deps = self.resolve_dependencies(payload, context)
        fields = {k: v for k, v in payload.items() if hasattr(Model, k)}
        fields.update(deps)
        if "institution_id" not in fields and context.tenant_id and context.tenant_id != "default":
            fields["institution_id"] = context.tenant_id
        period = Model.objects.create(**fields)
        return EntityPersistenceResult(
            node_id=payload.get("node_id", ""),
            entity_name=self.entity_name,
            orm_id=str(period.pk),
            created=True,
            success=True,
            duration_ms=_get_duration_ms(start),
        )

    def update(
        self,
        existing_instance: Any,
        payload: Dict[str, Any],
        context: PersistenceContext,
    ) -> EntityPersistenceResult:
        start = time.perf_counter()
        for k, v in payload.items():
            if hasattr(existing_instance, k) and k not in ("id", "pk", "academic_year", "institution"):
                setattr(existing_instance, k, v)
        existing_instance.save()
        return EntityPersistenceResult(
            node_id=payload.get("node_id", ""),
            entity_name=self.entity_name,
            orm_id=str(existing_instance.pk),
            created=False,
            success=True,
            duration_ms=_get_duration_ms(start),
        )


class EnrollmentRepository(BaseRepository):
    """Repository managing `academic.models.Enrollment` entities."""

    entity_name: str = "Enrollment"

    def _get_model(self):
        from academic.models import Enrollment
        return Enrollment

    def resolve_dependencies(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> Dict[str, Any]:
        resolved = {}
        for k in ("student", "student_id", "course", "course_id"):
            if k in context.resolved_dependencies:
                resolved[k] = context.resolved_dependencies[k]
            elif k in payload:
                resolved[k] = payload[k]
        if "student" not in resolved and "student_id" not in resolved:
            student_id = _extract_from_step_outputs(context, "Student")
            if student_id:
                resolved["student_id"] = student_id
        if "course" not in resolved and "course_id" not in resolved:
            course_id = _extract_from_step_outputs(context, "Course")
            if course_id:
                resolved["course_id"] = course_id
        if "institution" not in resolved and "institution_id" not in resolved:
            if context.tenant_id and context.tenant_id != "default":
                resolved["institution_id"] = context.tenant_id
            else:
                inst_id = _extract_from_step_outputs(context, "Institution")
                if inst_id:
                    resolved["institution_id"] = inst_id
        return resolved

    def validate_constraints(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> List[str]:
        errors = []
        deps = self.resolve_dependencies(payload, context)
        if "student" not in deps and "student_id" not in deps:
            errors.append("Enrollment requires a resolved 'student' or 'student_id'.")
        if "course" not in deps and "course_id" not in deps:
            errors.append("Enrollment requires a resolved 'course' or 'course_id'.")
        return errors

    def find_existing(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> Optional[Any]:
        Model = self._get_model()
        if "orm_id" in payload and payload["orm_id"]:
            return Model.objects.filter(pk=payload["orm_id"]).first()
        deps = self.resolve_dependencies(payload, context)
        qs = Model.objects.all()
        if context.tenant_id and context.tenant_id != "default":
            qs = qs.filter(institution_id=context.tenant_id)
        if "student" in deps and "course" in deps:
            return qs.filter(student=deps["student"], course=deps["course"]).first()
        if "student_id" in deps and "course_id" in deps:
            return qs.filter(student_id=deps["student_id"], course_id=deps["course_id"]).first()
        return None

    def create(
        self, payload: Dict[str, Any], context: PersistenceContext
    ) -> EntityPersistenceResult:
        start = time.perf_counter()
        Model = self._get_model()
        deps = self.resolve_dependencies(payload, context)
        fields = {k: v for k, v in payload.items() if hasattr(Model, k)}
        fields.update(deps)
        if "institution_id" not in fields and context.tenant_id and context.tenant_id != "default":
            fields["institution_id"] = context.tenant_id
        enrollment = Model.objects.create(**fields)
        return EntityPersistenceResult(
            node_id=payload.get("node_id", ""),
            entity_name=self.entity_name,
            orm_id=str(enrollment.pk),
            created=True,
            success=True,
            duration_ms=_get_duration_ms(start),
        )

    def update(
        self,
        existing_instance: Any,
        payload: Dict[str, Any],
        context: PersistenceContext,
    ) -> EntityPersistenceResult:
        start = time.perf_counter()
        for k, v in payload.items():
            if hasattr(existing_instance, k) and k not in ("id", "pk", "student", "course", "institution"):
                setattr(existing_instance, k, v)
        existing_instance.save()
        return EntityPersistenceResult(
            node_id=payload.get("node_id", ""),
            entity_name=self.entity_name,
            orm_id=str(existing_instance.pk),
            created=False,
            success=True,
            duration_ms=_get_duration_ms(start),
        )


__all__ = [
    "InstitutionRepository",
    "CourseRepository",
    "StudentRepository",
    "RepresentativeRepository",
    "AcademicPeriodRepository",
    "EnrollmentRepository",
]

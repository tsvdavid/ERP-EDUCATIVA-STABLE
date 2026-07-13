# apps/data_engine/templates/packaging/migration.py
"""Declarative data migrator to translate legacy import formats across template versions."""

from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Dict, List
from apps.data_engine.templates.packaging.exceptions import MigrationException


class TemplateMigrator:
    """Orchestrates in-flight data migrations to translate legacy inputs into active version formats."""

    def __init__(self) -> None:
        # Structure: {template_code: {(from_version, to_version): rules_dict_or_callable}}
        self._registry: Dict[str, Dict[tuple, Any]] = {}

    def register_migration(
        self,
        template_code: str,
        from_version: str,
        to_version: str,
        rules_or_func: Any,
    ) -> None:
        """Register a declarative migration rule dictionary or custom transformer function."""
        if not template_code:
            raise ValueError("template_code cannot be empty.")
        if not from_version or not to_version:
            raise ValueError("Versions cannot be empty.")

        key = (from_version.strip(), to_version.strip())
        self._registry.setdefault(template_code.strip(), {})[key] = rules_or_func

    def migrate(
        self,
        template_code: str,
        from_version: str,
        to_version: str,
        records: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Apply registered migrations sequentially to transform records from legacy to target version schema."""
        if from_version == to_version:
            return [dict(r) for r in records]

        t_registry = self._registry.get(template_code)
        if not t_registry:
            raise MigrationException(f"No migrations registered for template '{template_code}'.")

        key = (from_version, to_version)
        rule = t_registry.get(key)
        if not rule:
            # Try to resolve multi-step hop migrations (e.g. 1.0.0 -> 1.1.0 -> 1.2.0)
            # Find a path from from_version to to_version
            path = self._find_migration_path(t_registry, from_version, to_version)
            if not path:
                raise MigrationException(
                    f"No migration path resolved from '{from_version}' to '{to_version}' for template '{template_code}'."
                )
            
            current_records = [dict(r) for r in records]
            for step_from, step_to in path:
                current_records = self.migrate(template_code, step_from, step_to, current_records)
            return current_records

        # Execute migration
        migrated: List[Dict[str, Any]] = []
        for record in records:
            try:
                migrated.append(self._apply_migration_rule(record, rule))
            except Exception as exc:
                raise MigrationException(
                    f"Failed applying migration from '{from_version}' to '{to_version}' for template '{template_code}': {exc}"
                ) from exc
        return migrated

    def _find_migration_path(self, steps: Dict[tuple, Any], start: str, end: str) -> List[tuple]:
        """BFS pathfinding to chain version hops together."""
        queue = [[start]]
        visited = {start}
        
        # Build adjacency graph
        adj = {}
        for (f, t) in steps.keys():
            adj.setdefault(f, []).append(t)
            
        while queue:
            path = queue.pop(0)
            node = path[-1]
            if node == end:
                return [(path[i], path[i+1]) for i in range(len(path)-1)]
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])
        return []

    def _apply_migration_rule(self, record: Dict[str, Any], rule: Any) -> Dict[str, Any]:
        if callable(rule):
            return rule(record)

        if not isinstance(rule, dict):
            raise TypeError("Migration rule must be a dictionary or a callable transformer.")

        new_rec = dict(record)

        # 1. Deletions
        for f in rule.get("deletions", []):
            new_rec.pop(f, None)

        # 2. Renames
        for old, new in rule.get("renames", {}).items():
            if old in new_rec:
                new_rec[new] = new_rec.pop(old)

        # 3. Defaults
        for field, default_val in rule.get("defaults", {}).items():
            if field not in new_rec or new_rec[field] is None:
                new_rec[field] = default_val

        # 4. Conversions
        for field, conv_type in rule.get("conversions", {}).items():
            if field in new_rec and new_rec[field] is not None:
                val = new_rec[field]
                try:
                    if conv_type == "int":
                        new_rec[field] = int(val)
                    elif conv_type == "float":
                        new_rec[field] = float(val)
                    elif conv_type == "str":
                        new_rec[field] = str(val)
                    elif conv_type == "Decimal":
                        new_rec[field] = Decimal(str(val))
                    elif conv_type == "lower":
                        new_rec[field] = str(val).lower()
                    elif conv_type == "upper":
                        new_rec[field] = str(val).upper()
                    elif conv_type == "trim":
                        new_rec[field] = str(val).strip()
                except (ValueError, TypeError, InvalidOperation) as exc:
                    raise ValueError(f"Failed casting field '{field}' to type '{conv_type}': {exc}")

        return new_rec

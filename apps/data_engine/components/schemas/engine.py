from typing import Any, List, Dict
import datetime

from apps.data_engine.components.base import BaseComponent, MacContext
from apps.data_engine.components.rules.base import BaseRule
from apps.data_engine.components.rules.basic_rules import (
    RequiredRule, TypeRule, LengthRule, RangeRule, PatternRule
)

class RuleFactory:
    """Creates rule instances from a dictionary configuration."""
    
    TYPE_MAP = {
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "date": datetime.date,
        "datetime": datetime.datetime
    }

    @staticmethod
    def create(config: Dict[str, Any]) -> BaseRule:
        rule_type = config.get("rule")
        if not rule_type:
            raise ValueError("Rule configuration must specify 'rule' type.")
            
        if rule_type == "required":
            return RequiredRule()
            
        elif rule_type == "type":
            expected = config.get("expected_type")
            if expected not in RuleFactory.TYPE_MAP:
                raise ValueError(f"Unknown type '{expected}' for TypeRule.")
            return TypeRule(expected_type=RuleFactory.TYPE_MAP[expected])
            
        elif rule_type == "length":
            return LengthRule(
                min_length=config.get("min_length"),
                max_length=config.get("max_length")
            )
            
        elif rule_type == "range":
            return RangeRule(
                min_value=config.get("min_value"),
                max_value=config.get("max_value")
            )
            
        elif rule_type == "pattern":
            pattern = config.get("pattern")
            if not pattern:
                raise ValueError("PatternRule requires a 'pattern' argument.")
            return PatternRule(pattern=pattern)
            
        else:
            raise ValueError(f"Unknown rule type: '{rule_type}'")

class SchemaEngine:
    """Evaluates payload data against a configured schema of rules."""
    
    def __init__(self, schema_config: Dict[str, List[Dict[str, Any]]]):
        """
        Args:
            schema_config: e.g., {"age": [{"rule": "required"}, {"rule": "range", "min_value": 0}]}
        """
        self.schema: Dict[str, List[BaseRule]] = {}
        for field, rules_config in schema_config.items():
            self.schema[field] = [RuleFactory.create(r) for r in rules_config]
            
    def evaluate(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Evaluate the rules against the data and return a list of error dicts."""
        errors = []
        for index, row in enumerate(data):
            if not isinstance(row, dict):
                continue
                
            for field, rules in self.schema.items():
                value = row.get(field)
                for rule in rules:
                    error_msg = rule.validate(field, value)
                    if error_msg:
                        errors.append({
                            "row": index,
                            "field": field,
                            "error": error_msg
                        })
        return errors

class SchemaValidatorComponent(BaseComponent):
    """Adapter to integrate the SchemaEngine into the MAC pipeline."""
    component_type = "validator"
    
    def execute(self, context: MacContext) -> MacContext:
        schema_config = context.get("metadata", {}).get("validation_schema", {})
        if not schema_config:
            return context
            
        engine = SchemaEngine(schema_config=schema_config)
        payload = context.get("payload", [])
        
        errors = engine.evaluate(payload)
        
        if errors:
            if "metadata" not in context:
                context["metadata"] = {}
            if "validation_errors" not in context["metadata"]:
                context["metadata"]["validation_errors"] = []
            context["metadata"]["validation_errors"].extend(errors)
            
        return context

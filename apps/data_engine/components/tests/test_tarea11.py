import pytest
from apps.data_engine.components.rules.basic_rules import RequiredRule, TypeRule, LengthRule, RangeRule, PatternRule
from apps.data_engine.components.schemas.engine import SchemaEngine, SchemaValidatorComponent, RuleFactory
from apps.data_engine.components.base import MacContext

def test_required_rule():
    rule = RequiredRule()
    assert rule.validate("name", None) is not None
    assert rule.validate("name", "   ") is not None
    assert rule.validate("name", "Alice") is None

def test_type_rule():
    rule = TypeRule(expected_type=int)
    assert rule.validate("age", "25") is not None
    assert rule.validate("age", 25) is None
    assert rule.validate("age", None) is None # type rule ignores None

def test_length_rule():
    rule = LengthRule(min_length=3, max_length=5)
    assert rule.validate("code", "AB") is not None
    assert rule.validate("code", "ABCDEF") is not None
    assert rule.validate("code", "ABCD") is None
    assert rule.validate("code", 123) is not None # must be string

def test_range_rule():
    rule = RangeRule(min_value=10, max_value=20)
    assert rule.validate("score", 5) is not None
    assert rule.validate("score", 25) is not None
    assert rule.validate("score", 15) is None
    assert rule.validate("score", "15") is not None # must be number

def test_pattern_rule():
    rule = PatternRule(pattern=r"^[A-Z]{3}$")
    assert rule.validate("code", "abc") is not None
    assert rule.validate("code", "ABC") is None
    assert rule.validate("code", "ABCD") is not None

def test_rule_factory():
    rule = RuleFactory.create({"rule": "range", "min_value": 0, "max_value": 100})
    assert isinstance(rule, RangeRule)
    assert rule.min_value == 0
    assert rule.max_value == 100
    
    with pytest.raises(ValueError):
        RuleFactory.create({"rule": "unknown"})

def test_schema_engine():
    schema = {
        "age": [{"rule": "required"}, {"rule": "type", "expected_type": "int"}, {"rule": "range", "min_value": 0}],
        "name": [{"rule": "required"}, {"rule": "length", "min_length": 2}]
    }
    engine = SchemaEngine(schema)
    
    data = [
        {"age": 25, "name": "Alice"}, # Valid
        {"age": -5, "name": "B"},     # Invalid age range, invalid name length
        {"name": "Bob"}               # Missing age (required)
    ]
    
    errors = engine.evaluate(data)
    assert len(errors) == 3
    
    assert errors[0]["row"] == 1
    assert errors[0]["field"] == "age"
    
    assert errors[1]["row"] == 1
    assert errors[1]["field"] == "name"
    
    assert errors[2]["row"] == 2
    assert errors[2]["field"] == "age"

def test_schema_validator_component():
    comp = SchemaValidatorComponent()
    ctx: MacContext = {
        "payload": [{"code": "A"}],
        "metadata": {
            "validation_schema": {
                "code": [{"rule": "length", "min_length": 3}]
            }
        }
    }
    
    res = comp.execute(ctx)
    errors = res["metadata"]["validation_errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "code"

import pytest
from datetime import date
from apps.data_engine.components.mappers.dynamic_mapper import DynamicMapper, DynamicMapperComponent
from apps.data_engine.components.casters.type_caster import TypeCaster, TypeCasterComponent
from apps.data_engine.components.base import MacContext

def test_dynamic_mapper():
    mapper = DynamicMapper(strict_mapping=False)
    data = [
        {"Cédula": "123", "Nombre": "Alice", "Extra": "Ignored"}
    ]
    config = {"Cédula": "national_id", "Nombre": "first_name"}
    
    mapped_data = mapper.map(data, config)
    assert len(mapped_data) == 1
    assert mapped_data[0]["national_id"] == "123"
    assert mapped_data[0]["first_name"] == "Alice"
    assert mapped_data[0]["Extra"] == "Ignored" # Kept because strict is False

def test_dynamic_mapper_strict():
    mapper = DynamicMapper(strict_mapping=True)
    data = [{"Cédula": "123", "Extra": "Ignored"}]
    config = {"Cédula": "national_id"}
    
    mapped_data = mapper.map(data, config)
    assert "Extra" not in mapped_data[0]

def test_dynamic_mapper_component():
    comp = DynamicMapperComponent()
    ctx: MacContext = {
        "payload": [{"Cédula": "123"}], 
        "metadata": {"mapping_config": {"Cédula": "national_id"}, "strict_mapping": True}
    }
    res = comp.execute(ctx)
    assert res["payload"][0]["national_id"] == "123"

def test_type_caster_success():
    caster = TypeCaster()
    data = [
        {"age": "25", "is_active": "true", "birth_date": "2000-01-01", "name": "Bob"}
    ]
    schema = {"age": "int", "is_active": "bool", "birth_date": "date"}
    
    casted_data, errors = caster.cast(data, schema)
    
    assert len(errors) == 0
    assert casted_data[0]["age"] == 25
    assert casted_data[0]["is_active"] is True
    assert isinstance(casted_data[0]["birth_date"], date)
    assert casted_data[0]["name"] == "Bob"

def test_type_caster_failure():
    caster = TypeCaster()
    data = [
        {"age": "twenty-five", "is_active": "yes", "birth_date": "invalid-date"}
    ]
    schema = {"age": "int", "is_active": "bool", "birth_date": "date"}
    
    casted_data, errors = caster.cast(data, schema)
    
    assert len(errors) == 2 # age and birth_date failed
    assert errors[0]["field"] == "age"
    assert errors[1]["field"] == "birth_date"
    
    # Original values are kept on failure
    assert casted_data[0]["age"] == "twenty-five"
    assert casted_data[0]["is_active"] is True # 'yes' successfully casts to True

def test_type_caster_component():
    comp = TypeCasterComponent()
    ctx: MacContext = {
        "payload": [{"age": "abc"}],
        "metadata": {"schema_config": {"age": "int"}}
    }
    res = comp.execute(ctx)
    
    assert res["payload"][0]["age"] == "abc"
    errors = res["metadata"]["validation_errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "age"

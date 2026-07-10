import pytest
from apps.data_engine.components.readers.csv_reader import CSVReader, CSVReaderComponent
from apps.data_engine.components.parsers.csv_parser import CSVParser, CSVParserComponent
from apps.data_engine.components.validators.required_fields_validator import RequiredFieldsValidator, RequiredFieldsValidatorComponent
from apps.data_engine.components.validators.empty_rows_validator import EmptyRowsValidator, EmptyRowsValidatorComponent
from apps.data_engine.components.results.processing_result import ProcessingResult
from apps.data_engine.components.base import MacContext

def test_csv_reader():
    reader = CSVReader()
    csv_str = "id,name\n1, Alice \n2,Bob"
    data = reader.read(csv_str)
    assert len(data) == 2
    assert data[0]["name"] == " Alice "

def test_csv_reader_component():
    comp = CSVReaderComponent()
    ctx: MacContext = {"payload": "id,name\n1, Alice \n2,Bob"}
    res = comp.execute(ctx)
    assert len(res["payload"]) == 2

def test_csv_parser():
    parser = CSVParser()
    raw_data = [{"id": "1", "name": " Alice "}, {"id": "2", "name": "Bob"}]
    parsed = parser.parse(raw_data)
    assert parsed[0]["name"] == "Alice"
    assert parsed[1]["name"] == "Bob"

def test_csv_parser_component():
    comp = CSVParserComponent()
    ctx: MacContext = {"payload": [{"id": "1", "name": " Alice "}]}
    res = comp.execute(ctx)
    assert res["payload"][0]["name"] == "Alice"

def test_required_fields_validator():
    validator = RequiredFieldsValidator(required_fields=["id", "name"])
    data = [{"id": "1", "name": "Alice"}, {"id": "2", "name": ""}, {"id": "3"}]
    errors = validator.validate(data)
    assert len(errors) == 2
    assert errors[0]["row"] == 1
    assert errors[0]["field"] == "name"
    assert errors[1]["row"] == 2
    assert errors[1]["field"] == "name"

def test_required_fields_validator_component():
    comp = RequiredFieldsValidatorComponent()
    ctx: MacContext = {
        "payload": [{"id": "1"}], 
        "metadata": {"required_fields": ["id", "name"]}
    }
    res = comp.execute(ctx)
    errors = res["metadata"]["validation_errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "name"

def test_empty_rows_validator():
    validator = EmptyRowsValidator()
    data = [{"id": "1"}, {"id": "", "name": "  "}, {}]
    errors = validator.validate(data)
    assert len(errors) == 2
    assert errors[0]["row"] == 1
    assert errors[1]["row"] == 2

def test_empty_rows_validator_component():
    comp = EmptyRowsValidatorComponent()
    ctx: MacContext = {"payload": [{"id": ""}]}
    res = comp.execute(ctx)
    errors = res["metadata"]["validation_errors"]
    assert len(errors) == 1

def test_processing_result_success():
    ctx: MacContext = {"payload": [{"id": "1"}], "metadata": {}}
    result = ProcessingResult.from_context(ctx)
    assert result.success is True
    assert len(result.data) == 1

def test_processing_result_failure():
    ctx: MacContext = {
        "payload": [], 
        "metadata": {"validation_errors": [{"row": 0, "error": "test"}]}
    }
    result = ProcessingResult.from_context(ctx)
    assert result.success is False
    assert len(result.errors) == 1

from src.gdpr_obfuscator import obfuscate_jsonl
from io import BytesIO
import json
from pytest import raises


def test_obfuscate_jsonl_returns_a_bytesio_object():
    jsonl_content = {"headers": "content"}
    jsonl_str = json.dumps(jsonl_content)
    input_bytes = BytesIO(jsonl_str.encode("utf-8"))
    pii_fields = []
    output = obfuscate_jsonl(input_bytes, pii_fields)
    assert isinstance(output, BytesIO)


def test_obfuscate_jsonl_returns_the_same_contents_when_pii_fields_are_empty():
    jsonl_content = {"headers": "content"}
    jsonl_str = json.dumps(jsonl_content) + "\n"
    input_bytes = BytesIO(jsonl_str.encode("utf-8"))
    pii_fields = []
    output = obfuscate_jsonl(input_bytes, pii_fields)
    result = output.read().decode("utf-8")
    assert result == jsonl_str


def test_obfuscate_jsonl_returns_empty_byte_object_when_jsonl_has_no_body():
    jsonl_content = ""
    input_bytes = BytesIO(jsonl_content.encode("utf-8"))
    pii_fields = []
    output = obfuscate_jsonl(input_bytes, pii_fields)
    result = output.read().decode("utf-8")
    assert result == ""


def test_obfuscate_jsonl_hides_info_of_a_jsonl_with_one_line():
    jsonl_content = {"age": 31, "email": "fake@email.com", "name": "Fake Namington"}
    expected_jsonl = {"age": 31, "email": "***", "name": "***"}
    jsonl_str = json.dumps(jsonl_content)
    expected = json.dumps(expected_jsonl) + "\n"
    input_bytes = BytesIO(jsonl_str.encode("utf-8"))
    pii_fields = ["email", "name"]

    output = obfuscate_jsonl(input_bytes, pii_fields)
    result = output.read().decode("utf-8")
    assert result == expected


def test_obfuscate_jsonl_hides_info_of_a_jsonl_with_multiple_lines():
    jsonl_lines = [
        {"age": 31, "email": "fake@email.com", "name": "Fake Namington"},
        {"age": 10, "email": "bart@email.com", "name": "Bart Simpson"},
        {"age": 10, "email": "Milhouse@email.com", "name": "Milhouse van Houten"},
        {"age": 44, "email": "Skinner@email.com", "name": "Seymour Skinner"},
    ]
    jsonl_str = ""
    expected = ""
    for line in jsonl_lines:
        jsonl_str += json.dumps(line) + "\n"
        line["name"] = "***"
        line["email"] = "***"
        expected += json.dumps(line) + "\n"

    input_bytes = BytesIO(jsonl_str.encode("utf-8"))
    pii_fields = ["email", "name"]

    output = obfuscate_jsonl(input_bytes, pii_fields)
    result = output.read().decode("utf-8")

    assert result == expected


def test_obfuscate_jsonl_raises_error_if_pii_field_is_not_a_header():
    jsonl_content = {
        "age": 31,
        "email": "fake@email.com",
        "date of birth": "10,1981-04-01",
    }
    jsonl_str = json.dumps(jsonl_content)
    input_bytes = BytesIO(jsonl_str.encode("utf-8"))
    pii_fields = ["email", "name"]
    with raises(ValueError) as err:
        obfuscate_jsonl(input_bytes, pii_fields)
    assert str(err.value) == "The pii_field 'name' not found in headers."

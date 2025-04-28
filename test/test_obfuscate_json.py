from src.gdpr_obfuscator import obfuscate_json
from io import BytesIO
import json
from pytest import raises


def test_obfuscate_json_returns_a_bytesio_object():
    json_content = [{"headers": "content"}]
    json_str = json.dumps(json_content)
    input_bytes = BytesIO(json_str.encode("utf-8"))
    pii_fields = []
    output = obfuscate_json(input_bytes, pii_fields)
    assert isinstance(output, BytesIO)


def test_obfuscate_json_returns_the_same_contents_when_pii_fields_are_empty():
    pii_fields = []
    json_content_1 = [{"headers": "content"}]
    json_str_1 = json.dumps(json_content_1)
    input_bytes_1 = BytesIO(json_str_1.encode("utf-8"))
    output_1 = obfuscate_json(input_bytes_1, pii_fields)
    result_1 = output_1.read().decode("utf-8")
    assert result_1 == json_str_1

    json_content_2 = {"outer": [{"headers": "content"}]}
    json_str_2 = json.dumps(json_content_2)
    input_bytes_2 = BytesIO(json_str_2.encode("utf-8"))
    output_2 = obfuscate_json(input_bytes_2, pii_fields)
    result_2 = output_2.read().decode("utf-8")
    assert result_2 == json_str_2


def test_obfuscate_json_returns_empty_byte_object_when_json_has_no_body():
    pii_fields = []
    json_content_1 = []
    json_str_1 = json.dumps(json_content_1)
    input_bytes_1 = BytesIO(json_str_1.encode("utf-8"))
    output_1 = obfuscate_json(input_bytes_1, pii_fields)
    result_1 = output_1.read().decode("utf-8")
    assert result_1 == json_str_1

    json_content_2 = {}
    json_str_2 = json.dumps(json_content_2)
    input_bytes_2 = BytesIO(json_str_2.encode("utf-8"))
    output_2 = obfuscate_json(input_bytes_2, pii_fields)
    result_2 = output_2.read().decode("utf-8")
    assert result_2 == json_str_2


def test_obfuscate_json_hides_info_of_a_json_with_one_line():
    pii_fields = ["email", "name"]
    json_content_1 = [{"age": 31, "email": "fake@email.com", "name": "Fake Namington"}]
    expected_json_1 = [{"age": 31, "email": "***", "name": "***"}]
    json_str_1 = json.dumps(json_content_1)
    expected_1 = json.dumps(expected_json_1)
    input_bytes_1 = BytesIO(json_str_1.encode("utf-8"))

    output_1 = obfuscate_json(input_bytes_1, pii_fields)
    result_1 = output_1.read().decode("utf-8")
    assert result_1 == expected_1

    json_content_2 = {
        "outer": [{"age": 31, "email": "fake@email.com", "name": "Fake Namington"}]
    }
    expected_json_2 = {"outer": [{"age": 31, "email": "***", "name": "***"}]}
    json_str_2 = json.dumps(json_content_2)
    expected_2 = json.dumps(expected_json_2)
    input_bytes_2 = BytesIO(json_str_2.encode("utf-8"))

    output_2 = obfuscate_json(input_bytes_2, pii_fields)
    result_2 = output_2.read().decode("utf-8")
    assert result_2 == expected_2


def test_obfuscate_json_hides_info_of_a_json_with_multiple_lines():
    pii_fields = ["email", "name"]
    json_lines_1 = [
        {"age": 31, "email": "fake@email.com", "name": "Fake Namington"},
        {"age": 10, "email": "bart@email.com", "name": "Bart Simpson"},
        {"age": 10, "email": "Milhouse@email.com", "name": "Milhouse van Houten"},
        {"age": 44, "email": "Skinner@email.com", "name": "Seymour Skinner"},
    ]
    expected_line_1 = [
        {"age": 31, "email": "***", "name": "***"},
        {"age": 10, "email": "***", "name": "***"},
        {"age": 10, "email": "***", "name": "***"},
        {"age": 44, "email": "***", "name": "***"},
    ]
    json_str_1 = json.dumps(json_lines_1)
    expected_1 = json.dumps(expected_line_1)

    input_bytes_1 = BytesIO(json_str_1.encode("utf-8"))

    output_1 = obfuscate_json(input_bytes_1, pii_fields)
    result_1 = output_1.read().decode("utf-8")

    assert result_1 == expected_1

    json_lines_2 = {
        "outer": [
            {"age": 31, "email": "fake@email.com", "name": "Fake Namington"},
            {"age": 10, "email": "bart@email.com", "name": "Bart Simpson"},
            {"age": 10, "email": "Milhouse@email.com", "name": "Milhouse van Houten"},
            {"age": 44, "email": "Skinner@email.com", "name": "Seymour Skinner"},
        ]
    }
    expected_line_2 = {
        "outer": [
            {"age": 31, "email": "***", "name": "***"},
            {"age": 10, "email": "***", "name": "***"},
            {"age": 10, "email": "***", "name": "***"},
            {"age": 44, "email": "***", "name": "***"},
        ]
    }
    json_str_2 = json.dumps(json_lines_2)
    expected_2 = json.dumps(expected_line_2)

    input_bytes_2 = BytesIO(json_str_2.encode("utf-8"))

    output_2 = obfuscate_json(input_bytes_2, pii_fields)
    result_2 = output_2.read().decode("utf-8")

    assert result_2 == expected_2


def test_obfuscate_json_raises_error_if_pii_field_is_not_a_header():
    pii_fields = ["email", "name"]
    json_content_1 = [
        {
            "age": 31,
            "email": "fake@email.com",
            "date of birth": "10,1981-04-01",
        }
    ]
    json_str_1 = json.dumps(json_content_1)
    input_bytes_1 = BytesIO(json_str_1.encode("utf-8"))
    with raises(ValueError) as err:
        obfuscate_json(input_bytes_1, pii_fields)
    assert str(err.value) == "The pii_field 'name' not found in headers."

    json_content_2 = {
        "outer": [
            {
                "age": 31,
                "email": "fake@email.com",
                "date of birth": "10,1981-04-01",
            }
        ]
    }
    json_str_2 = json.dumps(json_content_2)
    input_bytes_2 = BytesIO(json_str_2.encode("utf-8"))
    with raises(ValueError) as err:
        obfuscate_json(input_bytes_2, pii_fields)
    assert str(err.value) == "The pii_field 'name' not found in headers."


def test_obfuscate_json_raises_error_if_json_input_bytes_has_invalid_body():
    jsonl_content = ""
    input_bytes = BytesIO(jsonl_content.encode("utf-8"))
    pii_fields = []
    with raises(json.JSONDecodeError) as err:
        obfuscate_json(input_bytes, pii_fields)
    assert str(err.value) == "Expecting value: line 1 column 1 (char 0)"

from src.gdpr_obfuscator import obfuscate_csv
from io import BytesIO
from pytest import raises


def test_obfuscate_csv_returns_a_bytesio_object():
    csv_content = "headers\ncontent\n"
    input_bytes = BytesIO(csv_content.encode("utf-8"))
    pii_fields = []
    output = obfuscate_csv(input_bytes, pii_fields)
    assert isinstance(output, BytesIO)


def test_obfuscate_csv_returns_the_same_contents_when_pii_fields_are_empty():
    csv_content = "headers\ncontent\n"
    input_bytes = BytesIO(csv_content.encode("utf-8"))
    pii_fields = []
    output = obfuscate_csv(input_bytes, pii_fields)
    result = output.read().decode("utf-8")
    assert result == csv_content


def test_obfuscate_csv_returns_empty_byte_object_when_csv_has_no_body():
    csv_content = ""
    input_bytes = BytesIO(csv_content.encode("utf-8"))
    pii_fields = []
    output = obfuscate_csv(input_bytes, pii_fields)
    result = output.read().decode("utf-8")
    assert result == ""


def test_obfuscate_csv_returns_the_same_contents_when_the_csv_only_has_headers():
    csv_content = "age,email,address\n"
    input_bytes = BytesIO(csv_content.encode("utf-8"))
    pii_fields = ["email"]
    output = obfuscate_csv(input_bytes, pii_fields)
    result = output.read().decode("utf-8")
    assert result == csv_content


def test_obfuscate_csv_hides_info_of_a_csv_with_headers_and_one_line():
    csv_content = "age,email,name\n31,fake@email.com,Fake Namington\n"
    input_bytes = BytesIO(csv_content.encode("utf-8"))
    pii_fields = ["email", "name"]

    output = obfuscate_csv(input_bytes, pii_fields)
    result = output.read().decode("utf-8")
    assert result == "age,email,name\n31,***,***\n"


def test_obfuscate_csv_hides_info_of_a_csv_with_headers_and_multiple_lines():
    csv_content = (
        "age,email,name\n"
        + "31,fake@email.com,Fake Namington\n"
        + "10,bart@email.com,Bart Simpson\n"
        + "10,Milhouse@email.com,Milhouse van Houten\n"
        + "44,Skinner@email.com,Seymour Skinner\n"
    )
    input_bytes = BytesIO(csv_content.encode("utf-8"))
    pii_fields = ["email", "name"]

    output = obfuscate_csv(input_bytes, pii_fields)
    result = output.read().decode("utf-8")

    assert (
        result
        == "age,email,name\n"
        + "31,***,***\n"
        + "10,***,***\n"
        + "10,***,***\n"
        + "44,***,***\n"
    )


def test_obfuscate_csv_raises_error_if_pii_field_is_not_a_header():
    csv_content = "name,age,date of birth\n" + "Bart,10,1981-04-01\n"
    input_bytes = BytesIO(csv_content.encode("utf-8"))
    pii_fields = ["email", "name"]
    with raises(ValueError) as err:
        obfuscate_csv(input_bytes, pii_fields)
    assert str(err.value) == "The pii_fields '{'email'}' not found in headers."

from src.gdpr_obfuscator import gdpr_obfuscator, csv_string_to_list
from io import BytesIO
from boto3 import client
from botocore.exceptions import ClientError
from os import environ, getenv, path
import time
from pytest import raises, fixture, mark
from moto import mock_aws
from unittest.mock import patch


@fixture(scope="function")
def aws_credentials():
    environ["AWS_ACCESS_KEY_ID"] = "test"
    environ["AWS_SECRET_ACCESS_KEY"] = "test"
    environ["AWS_SECURITY_TOKEN"] = "test"
    environ["AWS_SESSION_TOKEN"] = "test"
    environ["AWS_DEFAULT_REGION"] = "eu-west-2"


@fixture(scope="function")
def s3_client(aws_credentials):
    with mock_aws():
        yield client("s3", region_name="eu-west-2")


@fixture(autouse=True)
def patch_s3_client(s3_client):
    with patch("src.gdpr_obfuscator.s3_client", s3_client):
        yield


@fixture
def s3_setup(s3_client):
    def _setup(bucket, key, body, file_path=False):
        s3_client.create_bucket(
            Bucket=bucket, CreateBucketConfiguration={"LocationConstraint": "eu-west-2"}
        )
        if file_path:
            with open(body, "rb") as f:
                s3_client.put_object(Bucket=bucket, Key=key, Body=f)
        else:
            s3_client.put_object(Bucket=bucket, Key=key, Body=body.encode("utf-8"))

    return _setup


def test_gdpr_obfuscator_returns_a_bytesio_object(s3_setup):
    bucket = "test-bucket"
    key = "test-key.csv"
    csv_content = "headers\ncontent\n"
    s3_setup(bucket, key, csv_content)
    event = {"file_to_obfuscate": f"s3://{bucket}/{key}", "pii_fields": []}
    output = gdpr_obfuscator(event)
    assert isinstance(output, BytesIO)


def test_gdpr_obfuscator_returns_the_same_contents_when_pii_fields_are_empty(s3_setup):
    bucket = "test-bucket"
    key = "test-key.csv"
    csv_content = "headers\ncontent\n"
    s3_setup(bucket, key, csv_content)
    event = {"file_to_obfuscate": f"s3://{bucket}/{key}", "pii_fields": []}
    output = gdpr_obfuscator(event)
    result = output.read().decode("utf-8")
    assert result == csv_content


def test_gdpr_obfuscator_returns_empty_byte_object_when_csv_has_no_body(s3_setup):
    bucket = "test-bucket"
    key = "test-key.csv"
    csv_content = ""
    s3_setup(bucket, key, csv_content)
    event = {
        "file_to_obfuscate": f"s3://{bucket}/{key}",
        "pii_fields": [],
    }
    output = gdpr_obfuscator(event)
    result = output.read().decode("utf-8")
    assert result == ""


def test_gdpr_obfuscator_returns_the_same_contents_when_the_csv_only_has_headers(
    s3_setup,
):
    bucket = "test-bucket"
    key = "test-key.csv"
    csv_content = "age,email,address\n"
    s3_setup(bucket, key, csv_content)
    event = {"file_to_obfuscate": f"s3://{bucket}/{key}", "pii_fields": ["email"]}
    output = gdpr_obfuscator(event)
    result = output.read().decode("utf-8")
    assert result == csv_content


def test_gdpr_obfuscator_hides_info_of_a_csv_with_headers_and_one_line(s3_setup):
    bucket = "test-bucket"
    key = "test-key.csv"
    csv_content = "age,email,name\n31,fake@email.com,Fake Namington\n"
    s3_setup(bucket, key, csv_content)
    event = {
        "file_to_obfuscate": f"s3://{bucket}/{key}",
        "pii_fields": ["email", "name"],
    }
    output = gdpr_obfuscator(event)
    result = output.read().decode("utf-8")
    assert result == "age,email,name\n31,***,***\n"


def test_gdpr_obfuscator_hides_info_of_a_csv_with_headers_and_multiple_lines(s3_setup):
    bucket = "test-bucket"
    key = "test-key.csv"
    csv_content = (
        "age,email,name\n"
        + "31,fake@email.com,Fake Namington\n"
        + "10,bart@email.com,Bart Simpson\n"
        + "10,Milhouse@email.com,Milhouse van Houten\n"
        + "44,Skinner@email.com,Seymour Skinner\n"
    )
    s3_setup(bucket, key, csv_content)
    event = {
        "file_to_obfuscate": f"s3://{bucket}/{key}",
        "pii_fields": ["email", "name"],
    }
    output = gdpr_obfuscator(event)
    result = output.read().decode("utf-8")
    assert (
        result
        == "age,email,name\n"
        + "31,***,***\n"
        + "10,***,***\n"
        + "10,***,***\n"
        + "44,***,***\n"
    )


def test_gdpr_obfuscator_raises_type_error_with_an_invalid_arg():
    event1 = "I'm a string not a dict"
    with raises(TypeError) as err:
        gdpr_obfuscator(event1)
    assert str(err.value) == "event must be a dictionary"

    event2 = {"Incorrect Key": None}
    with raises(TypeError) as err:
        gdpr_obfuscator(event2)
    assert (
        str(err.value)
        == "event must contain only the keys {'pii_fields', 'file_to_obfuscate'}"
    )

    event3 = {
        "Incorrect Key": None,
        "file_to_obfuscate": "s3://valid-bucket/valid-key.csv",
        "pii_fields": "I should be a list",
    }
    with raises(TypeError) as err:
        gdpr_obfuscator(event3)
    assert (
        str(err.value)
        == "event must contain only the keys {'pii_fields', 'file_to_obfuscate'}"
    )

    event4 = {
        "file_to_obfuscate": [],
        "pii_fields": ["email", "name"],
    }
    with raises(TypeError) as err:
        gdpr_obfuscator(event4)
    assert str(err.value) == "file_to_obfuscate value must be a string"

    event5 = {
        "file_to_obfuscate": "s3://valid-bucket/valid-key.csv",
        "pii_fields": "I should be a list",
    }
    with raises(TypeError) as err:
        gdpr_obfuscator(event5)
    assert str(err.value) == "pii_fields value must be a list of strings"

    event6 = {
        "file_to_obfuscate": "s3://valid-bucket/valid-key.csv",
        "pii_fields": [1, 2, 3],
    }
    with raises(TypeError) as err:
        gdpr_obfuscator(event6)
    assert str(err.value) == "pii_fields value must be a list of strings"


def test_gdpr_obfuscator_raises_client_error_when_bucket_doesnt_exist():
    event = {"file_to_obfuscate": "s3://bad-bucket/key.csv", "pii_fields": []}
    with raises(ClientError) as err:
        gdpr_obfuscator(event)
    assert (
        str(err.value)
        == "An error occurred (NoSuchBucket) when calling the GetObject operation: The specified bucket does not exist"
    )


def test_gdpr_obfuscator_raises_client_error_when_key_doesnt_exist(s3_setup):
    bucket = "test-bucket"
    key = "test-key.csv"
    csv_content = (
        "age,email,name\n"
        + "31,fake@email.com,Fake Namington\n"
        + "10,bart@email.com,Bart Simpson\n"
        + "10,Milhouse@email.com,Milhouse van Houten\n"
        + "44,Skinner@email.com,Seymour Skinner\n"
    )
    s3_setup(bucket, key, csv_content)
    event = {
        "file_to_obfuscate": f"s3://{bucket}/bad_key.csv",
        "pii_fields": ["email", "name"],
    }
    with raises(ClientError) as err:
        gdpr_obfuscator(event)
    assert (
        str(err.value)
        == "An error occurred (NoSuchKey) when calling the GetObject operation: The specified key does not exist."
    )


def test_gdpr_obfuscator_raises_value_error_with_invalid_s3_uri():
    file1 = "bad-bucket/key.csv"
    event1 = {"file_to_obfuscate": file1, "pii_fields": []}
    with raises(ValueError) as err:
        gdpr_obfuscator(event1)
    assert str(err.value) == f"Invalid S3 URI: {file1}"

    file2 = "s3:///key.csv"
    event2 = {"file_to_obfuscate": file2, "pii_fields": []}
    with raises(ValueError) as err:
        gdpr_obfuscator(event2)
    assert str(err.value) == f"S3 URI must include bucket and key: {file2}"

    file3 = "s3://bad-bucket/"
    event3 = {"file_to_obfuscate": file3, "pii_fields": []}
    with raises(ValueError) as err:
        gdpr_obfuscator(event3)
    assert str(err.value) == f"S3 URI must include bucket and key: {file3}"


def test_gdpr_obuscator_raises_value_error_if_file_is_an_incorrect_format(s3_setup):
    bucket = "test-bucket"
    key = "test-key.txt"
    csv_content = "I'm not a csv..."
    s3_setup(bucket, key, csv_content)
    event = {
        "file_to_obfuscate": f"s3://{bucket}/{key}",
        "pii_fields": ["email", "name"],
    }
    with raises(ValueError) as err:
        gdpr_obfuscator(event)
    assert str(err.value) == "target file must be a csv"


def test_gdpr_obfuscator_raises_error_if_pii_field_is_not_a_header(s3_setup):
    bucket = "test-bucket"
    key = "test-key.csv"
    csv_content = "name,age,date of birth\n" + "Bart,10,1981-04-01\n"
    s3_setup(bucket, key, csv_content)
    event = {
        "file_to_obfuscate": f"s3://{bucket}/{key}",
        "pii_fields": ["email", "name"],
    }
    with raises(ValueError) as err:
        gdpr_obfuscator(event)
    assert str(err.value) == "pii_fields not found in {'email'}"


@mark.skipif(getenv("CI") == "true", reason="Skipped in CI environment")
def test_runtime_of_gpdr_obfuscator_is_less_than_one_minute_for_one_mb_of_data(
    s3_setup,
):
    bucket = "test-bucket"
    key = "test-key.csv"
    csv_content = "test-data/test_csv.csv"
    s3_setup(bucket, key, csv_content, True)

    with open("test-data/test_csv.csv", "r", encoding="utf-8") as f:
        heading_string = f.readline()
    headings = csv_string_to_list(heading_string)
    event = {"file_to_obfuscate": f"s3://{bucket}/{key}", "pii_fields": headings}
    t1 = time.time()
    gdpr_obfuscator(event)
    t2 = time.time()
    assert t2 - t1 <= 60


def test_module_size_doesnt_exceed_lambda_regulations():
    file_path = "src/gdpr_obfuscator.py"
    max_size_bytes = 250 * 1024 * 1024

    size = path.getsize(file_path)
    assert size < max_size_bytes

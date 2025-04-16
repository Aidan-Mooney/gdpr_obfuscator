from src.gdpr_obfuscator import gdpr_obfuscator
from io import BytesIO
from boto3 import client
from botocore.exceptions import ClientError
from os import environ
from pytest import raises, fixture
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
    def _setup(bucket, key, csv_content):
        s3_client.create_bucket(
            Bucket=bucket, CreateBucketConfiguration={"LocationConstraint": "eu-west-2"}
        )
        s3_client.put_object(Bucket=bucket, Key=key, Body=csv_content.encode("utf-8"))

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

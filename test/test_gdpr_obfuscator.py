from src.gdpr_obfuscator import gdpr_obfuscator, csv_string_to_list
from io import BytesIO
import json
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


@fixture(scope="function")
def patch_obfuscators():
    with (
        patch("src.gdpr_obfuscator.obfuscate_csv") as mock_csv,
        patch("src.gdpr_obfuscator.obfuscate_jsonl") as mock_jsonl,
        patch("src.gdpr_obfuscator.obfuscate_json") as mock_json,
    ):
        yield mock_csv, mock_jsonl, mock_json


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


class TestCoreFunctionalityOfGdprObfuscator:
    def test_gdpr_obfuscator_returns_a_bytesio_object(
        self, s3_setup, patch_obfuscators
    ):
        bucket = "test-bucket"
        key = "test-key.csv"
        csv_content = "headers\ncontent\n"
        s3_setup(bucket, key, csv_content)
        mock_csv, _, _ = patch_obfuscators
        mock_csv.return_value = BytesIO(csv_content.encode("utf-8"))

        event = {"file_to_obfuscate": f"s3://{bucket}/{key}", "pii_fields": []}
        output = gdpr_obfuscator(event)
        assert isinstance(output, BytesIO)

    def test_gdpr_obfuscator_triggers_obfuscate_csv(self, s3_setup, patch_obfuscators):
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
        expected = (
            "age,email,name\n"
            + "31,***,***\n"
            + "10,***,***\n"
            + "10,***,***\n"
            + "44,***,***\n"
        )
        mock_csv, _, _ = patch_obfuscators
        mock_csv.return_value = BytesIO(expected.encode("utf-8"))

        event = {"file_to_obfuscate": f"s3://{bucket}/{key}", "pii_fields": []}
        output = gdpr_obfuscator(event)
        result = output.read().decode("utf-8")

        assert result == expected

    def test_gdpr_obfuscator_triggers_obfuscate_jsonl(
        self, s3_setup, patch_obfuscators
    ):
        bucket = "test-bucket"
        key = "test-key.jsonl"
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
        s3_setup(bucket, key, jsonl_str)
        _, mock_jsonl, _ = patch_obfuscators
        mock_jsonl.return_value = BytesIO(expected.encode("utf-8"))

        event = {"file_to_obfuscate": f"s3://{bucket}/{key}", "pii_fields": []}
        output = gdpr_obfuscator(event)
        result = output.read().decode("utf-8")

        assert result == expected

    def test_gdpr_obfuscator_triggers_obfuscate_json(self, s3_setup, patch_obfuscators):
        bucket = "test-bucket"
        key = "test-key.json"
        jsonl_lines = [
            {"age": 31, "email": "fake@email.com", "name": "Fake Namington"},
            {"age": 10, "email": "bart@email.com", "name": "Bart Simpson"},
            {"age": 10, "email": "Milhouse@email.com", "name": "Milhouse van Houten"},
            {"age": 44, "email": "Skinner@email.com", "name": "Seymour Skinner"},
        ]
        expected_lines = [
            {"age": 31, "email": "***", "name": "***"},
            {"age": 10, "email": "***", "name": "***"},
            {"age": 10, "email": "***", "name": "***"},
            {"age": 44, "email": "***", "name": "***"},
        ]
        jsonl_str = json.dumps(jsonl_lines)
        expected_str = json.dumps(expected_lines)
        s3_setup(bucket, key, jsonl_str)
        _, _, mock_json = patch_obfuscators
        mock_json.return_value = BytesIO(expected_str.encode("utf-8"))

        event = {"file_to_obfuscate": f"s3://{bucket}/{key}", "pii_fields": []}

        output = gdpr_obfuscator(event)
        result = output.read().decode("utf-8")

        assert result == expected_str


class TestGpdrObfuscatorRaisesErrorsCorrectly:
    def test_gdpr_obfuscator_raises_type_error_with_an_invalid_arg(self):
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

    def test_gdpr_obfuscator_raises_client_error_when_bucket_doesnt_exist(self):
        event = {"file_to_obfuscate": "s3://bad-bucket/key.csv", "pii_fields": []}
        with raises(ClientError) as err:
            gdpr_obfuscator(event)
        assert (
            str(err.value)
            == "An error occurred (NoSuchBucket) when calling the GetObject operation: The specified bucket does not exist"
        )

    def test_gdpr_obfuscator_raises_client_error_when_key_doesnt_exist(self, s3_setup):
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

    def test_gdpr_obfuscator_raises_value_error_with_invalid_s3_uri(self):
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

    def test_gdpr_obuscator_raises_value_error_if_file_is_an_incorrect_format(
        self, s3_setup
    ):
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
        assert str(err.value) == "target file must be a csv or json"


@mark.skipif(getenv("CI") == "true", reason="Skipped in CI environment")
class TestGdprObfuscatorMeetsPerformanceAndNoneFunctionalCriteria:
    @mark.skipif(getenv("TEST_TYPE") != "csv", reason="Skipped unless TEST_TYPE=csv")
    def test_runtime_of_gpdr_obfuscator_is_less_than_one_minute_for_one_mb_of_csv_data(
        self,
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

    @mark.skipif(
        getenv("TEST_TYPE") != "jsonl", reason="Skipped unless TEST_TYPE=jsonl"
    )
    def test_runtime_of_gpdr_obfuscator_is_less_than_one_minute_for_one_mb_of_jsonl_data(
        self,
        s3_setup,
    ):
        bucket = "test-bucket"
        key = "test-key.jsonl"
        jsonl_content = "test-data/test_jsonl.jsonl"
        s3_setup(bucket, key, jsonl_content, True)

        with open("test-data/test_jsonl.jsonl", "r", encoding="utf-8") as f:
            first_line = json.loads(f.readline())
        keys_list = list(first_line.keys())
        event = {"file_to_obfuscate": f"s3://{bucket}/{key}", "pii_fields": keys_list}
        t1 = time.time()
        gdpr_obfuscator(event)
        t2 = time.time()
        assert t2 - t1 <= 60

    @mark.skipif(getenv("TEST_TYPE") != "json", reason="Skipped unless TEST_TYPE=json")
    def test_runtime_of_gpdr_obfuscator_is_less_than_one_minute_for_one_mb_of_json_data(
        self,
        s3_setup,
    ):
        bucket = "test-bucket"
        key = "test-key.json"
        jsonl_content = "test-data/test_json.json"
        s3_setup(bucket, key, jsonl_content, True)

        event = {
            "file_to_obfuscate": f"s3://{bucket}/{key}",
            "pii_fields": ["id", "text"],
        }
        t1 = time.time()
        gdpr_obfuscator(event)
        t2 = time.time()
        assert t2 - t1 <= 60

    def test_module_size_doesnt_exceed_lambda_regulations(self):
        file_path = "src/gdpr_obfuscator.py"
        max_size_bytes = 250 * 1024 * 1024

        size = path.getsize(file_path)
        assert size < max_size_bytes

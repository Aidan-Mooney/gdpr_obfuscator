from boto3 import client
from io import TextIOWrapper, BytesIO
import json

from typing import List, Tuple


s3_client = client("s3")


def gdpr_obfuscator(event: dict) -> BytesIO:
    """Obfuscate PII fields in a CSV file stored in S3.

    This function expects an event dictionary containing the S3 URI of the target CSV file
    and a list of PII fields to be obfuscated. It returns a `BytesIO` object containing
    the modified CSV content with specified fields replaced by '***'.

    Args:
        event (dict): A dictionary with the following keys:
            - 'file_to_obfuscate' (str): The S3 URI of the CSV file.
            - 'pii_fields' (List[str]): A list of field names to be obfuscated.

    Returns:
        BytesIO: A stream containing the obfuscated CSV file.

    Raises:
        TypeError: If `event` is not a dictionary or has invalid/missing fields.
        ValueError: If the file is not a CSV or the S3 URI is invalid.
    """
    if not isinstance(event, dict):
        raise TypeError("event must be a dictionary")
    expected_keys = {"file_to_obfuscate", "pii_fields"}
    actual_keys = set(event.keys())
    if actual_keys != expected_keys:
        raise TypeError(
            "event must contain only the keys {'pii_fields', 'file_to_obfuscate'}"
        )
    elif not isinstance(event["file_to_obfuscate"], str):
        raise TypeError("file_to_obfuscate value must be a string")
    elif not isinstance(event["pii_fields"], list) or any(
        not isinstance(x, str) for x in event["pii_fields"]
    ):
        raise TypeError("pii_fields value must be a list of strings")

    bucket, key = extract_bucket_key(event["file_to_obfuscate"])
    response = s3_client.get_object(Bucket=bucket, Key=key)

    file_types = [
        (".csv", obfuscate_csv),
        (".jsonl", obfuscate_jsonl),
        (".json", obfuscate_json),
    ]
    for file_type, obfuscate_func in file_types:
        if key.endswith(file_type):
            return obfuscate_func(response["Body"], event["pii_fields"])
    raise ValueError("target file must be a csv or json")


def obfuscate_csv(body: BytesIO, pii_fields: List[str]) -> BytesIO:
    """Obfuscate specified fields in a CSV file-like object.

    Reads a CSV input stream, replaces the values of specified PII fields with '***',
    and returns the modified content as a BytesIO stream.

    Args:
        body: A file-like object (e.g., BytesIO) containing the CSV data.
        pii_fields (List[str]): A list of header names to be obfuscated.

    Returns:
        BytesIO: A stream containing the obfuscated CSV data.

    Raises:
        ValueError: If any specified pii_fields are not found in the CSV header.
    """
    input_stream = TextIOWrapper(body, encoding="utf-8")

    output_buffer = BytesIO()

    header = input_stream.readline()
    col_nums = get_col_nums(csv_string_to_list(header), pii_fields)
    output_buffer.write(header.encode("utf-8"))

    for line in input_stream:
        output_buffer.write(edit_line(line, col_nums).encode("utf-8"))

    output_buffer.seek(0)
    return output_buffer


def obfuscate_jsonl(body: BytesIO, pii_fields: List[str]) -> BytesIO:
    """Obfuscate specified fields in a JSONL (JSON Lines) file-like object.

    Reads a stream of JSON objects (one per line), replaces the values of specified
    PII fields with '***', and returns the modified content as a BytesIO stream.

    Args:
        body: A file-like object (e.g., BytesIO) containing JSONL data.
        pii_fields (List[str]): A list of field names to be obfuscated in each JSON object.

    Returns:
        BytesIO: A stream containing the obfuscated JSONL data.

    Raises:
        ValueError: If a specified pii_field is not present in a JSON object.
    """
    input_stream = TextIOWrapper(body, encoding="utf-8")

    output_buffer = BytesIO()

    for line in input_stream:
        line_dict = json.loads(line)
        new_line_dict = line_dict.copy()
        for field in pii_fields:
            if field in line_dict:
                new_line_dict[field] = "***"
            else:
                raise ValueError(f"The pii_field '{field}' not found in headers.")
        new_line = json.dumps(new_line_dict) + "\n"
        output_buffer.write(new_line.encode("utf-8"))

    output_buffer.seek(0)
    return output_buffer


def obfuscate_json(body: BytesIO, pii_fields: List[str]) -> BytesIO:
    """Obfuscate specified fields in a JSON file-like object.

    Reads a JSON input stream, replaces the values of specified PII fields with '***',
    and returns the modified content as a BytesIO stream.

    Args:
        body: A file-like object (e.g., BytesIO) containing the JSON data.
        pii_fields (List[str]): A list of header names to be obfuscated.

    Returns:
        BytesIO: A stream containing the obfuscated JSON data.

    Raises:
        ValueError: If any specified pii_fields are not found in the JSON header.
        JSONDecodeError: If body contains invalid JSON.
    """
    file_content = json.load(body)
    output_buffer = BytesIO()
    if isinstance(file_content, dict):
        for key, value in file_content.items():
            for row in value:
                for field in pii_fields:
                    if field in row:
                        row[field] = "***"
                    else:
                        raise ValueError(
                            f"The pii_field '{field}' not found in headers."
                        )
    elif isinstance(file_content, list):
        for row in file_content:
            for field in pii_fields:
                if field in row:
                    row[field] = "***"
                else:
                    raise ValueError(f"The pii_field '{field}' not found in headers.")
    output_buffer.write(json.dumps(file_content).encode("utf-8"))
    output_buffer.seek(0)
    return output_buffer


def extract_bucket_key(s3_uri: str) -> Tuple[str, str]:
    """Extract the bucket name and key from an S3 URI.


    Args:
        s3_uri (str): The S3 URI in the format 's3://bucket/key'.


    Returns:
        Tuple[str, str]: A tuple containing the bucket name and key.


    Raises:
        ValueError: If the URI is not a valid S3 URI.
        ValueError: If the URI does not contain both a bucket and a key.
    """
    if not s3_uri.startswith("s3://"):
        raise ValueError(f"Invalid S3 URI: {s3_uri}")
    without_prefix = s3_uri[5:]
    parts = without_prefix.split("/", 1)
    if len(parts) != 2 or parts[0] == "" or parts[1] == "":
        raise ValueError(f"S3 URI must include bucket and key: {s3_uri}")
    bucket, key = parts
    return bucket, key


def csv_string_to_list(line: str) -> List[str]:
    """Convert a CSV-formatted string into a list of values.


    Args:
        line (str): A single line of CSV data.


    Returns:
        List[str]: A list of values parsed from the CSV line.
    """
    return line.strip().split(",")


def get_col_nums(headers: List[str], pii_fields: List[str]) -> List[int]:
    """Get the indices of PII fields in the CSV headers.


    Args:
        headers (List[str]): The list of CSV header names.
        pii_fields (List[str]): Field names that should be obfuscated.


    Returns:
        List[int]: Indices of the PII fields within the headers list.


    Raises:
        ValueError: If any PII field is not found in the headers.
    """
    fields_set = set(pii_fields)
    output = []
    found_fields = set()
    for index, item in enumerate(headers):
        if item in fields_set:
            output.append(index)
            found_fields.add(item)
    unfound_fields = fields_set - found_fields
    if not unfound_fields:
        return output
    else:
        raise (ValueError(f"The pii_fields '{unfound_fields}' not found in headers."))


def edit_line(line: str, col_nums: List[int]) -> str:
    """Obfuscate specific columns in a CSV line by replacing their values.


    Args:
        line (str): A single line of CSV data.
        col_nums (List[int]): Indices of the columns to obfuscate.


    Returns:
        str: The CSV line with specified columns replaced by '***'.
    """
    lst = csv_string_to_list(line)
    for num in col_nums:
        lst[num] = "***"
    return ",".join(lst) + "\n"

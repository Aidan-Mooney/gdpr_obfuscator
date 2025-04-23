from boto3 import client
from io import TextIOWrapper, BytesIO

from typing import List, Tuple


s3_client = client("s3")


def gdpr_obfuscator(event: dict) -> BytesIO:
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
    if not key.endswith(".csv"):
        raise ValueError("target file must be a csv")
    response = s3_client.get_object(Bucket=bucket, Key=key)
    input_stream = TextIOWrapper(response["Body"], encoding="utf-8")

    output_buffer = BytesIO()

    header = input_stream.readline()
    col_nums = get_col_nums(csv_string_to_list(header), event["pii_fields"])
    output_buffer.write(header.encode("utf-8"))

    for line in input_stream:
        output_buffer.write(edit_line(line, col_nums).encode("utf-8"))

    output_buffer.seek(0)
    return output_buffer


def extract_bucket_key(s3_uri: str) -> Tuple[str, str]:
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
        raise (ValueError(f"pii_fields not found in {unfound_fields}"))


def edit_line(line: str, col_nums: List[int]) -> str:
    lst = csv_string_to_list(line)
    for num in col_nums:
        lst[num] = "***"
    return ",".join(lst) + "\n"

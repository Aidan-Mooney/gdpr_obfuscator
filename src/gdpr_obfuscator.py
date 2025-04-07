from boto3 import client
from io import BytesIO

from typing import List, Tuple


s3_client = client("s3")


def gdpr_obfuscator(event: dict) -> BytesIO:
    return BytesIO()


def extract_bucket_key(s3_uri: str) -> Tuple[str, str]:
    if not s3_uri.startswith("s3://"):
        raise ValueError(f"Invalid S3 URI: {s3_uri}")
    without_prefix = s3_uri[5:]
    parts = without_prefix.split("/", 1)
    if len(parts) != 2 or parts[0] == "":
        raise ValueError(f"S3 URI must include bucket and key: {s3_uri}")
    bucket, key = parts
    return bucket, key


def csv_string_to_list(line: str) -> List[str]:
    return line.strip().split(",")


def list_to_csv_string(lst: List[str]) -> str:
    return ",".join(lst) + "\n"


def get_col_nums(header: str, pii_fields: List[str]) -> List[int]:
    return [index for index, item in enumerate(header) if item in pii_fields]


def edit_line(line: str, col_nums: List[int]) -> str:
    lst = csv_string_to_list(line)
    for num in col_nums:
        lst[num] = "***"
    return list_to_csv_string(lst)

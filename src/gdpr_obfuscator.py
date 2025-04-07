from boto3 import client
from io import BytesIO

from typing import List, Tuple


s3_client = client("s3")


def gdpr_obfuscator(event: dict) -> BytesIO:
    return BytesIO()


def extract_bucket_key(s3_path: str) -> Tuple[str, str]:
    return "", ""


def csv_string_to_list(line: str) -> List[str]:
    return []


def list_to_csv_string(lst: List[str]) -> str:
    return ""


def get_col_nums(header: str, pii_fields: List[str]) -> List[int]:
    return []


def edit_line(line: str, col_nums: List[int]) -> str:
    return ""

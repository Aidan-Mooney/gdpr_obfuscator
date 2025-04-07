from src.gdpr_obfuscator import extract_bucket_key


def test_extract_bucket_key_returns_a_tuple_of_two_strings():
    s3_path = "s3://test_bucket/new_data/file1.csv"
    output = extract_bucket_key(s3_path)
    assert isinstance(output, tuple)
    bucket, key = output
    assert isinstance(bucket, str)
    assert isinstance(key, str)

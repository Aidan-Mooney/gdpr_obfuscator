from src.gdpr_obfuscator import extract_bucket_key


from pytest import raises


def test_extract_bucket_key_returns_a_tuple_of_two_strings():
    test_uri = "s3://test_bucket/new_data/file1.csv"
    output = extract_bucket_key(test_uri)
    assert isinstance(output, tuple)
    bucket, key = output
    assert isinstance(bucket, str)
    assert isinstance(key, str)


def test_extract_bucket_key_splits_correctly_with_no_directory():
    test_uri = "s3://test_bucket/test_key.csv"
    bucket, key = extract_bucket_key(test_uri)
    assert bucket == "test_bucket"
    assert key == "test_key.csv"


def test_extract_bucket_key_splits_correctly_with_directory():
    test_uri = "s3://test_bucket/new_data/file1.csv"
    bucket, key = extract_bucket_key(test_uri)
    assert bucket == "test_bucket"
    assert key == "new_data/file1.csv"


def test_extract_bucket_key_raises_value_error_if_s3_uri_doesnt_start_with_the_correct_prefix():
    test_uri = "test_bucket/test_key.csv"
    with raises(ValueError) as err:
        extract_bucket_key(test_uri)
    assert str(err.value) == f"Invalid S3 URI: {test_uri}"


def test_extract_bucket_key_raises_value_error_if_provided_no_bucket():
    test_uri = "s3:///test_key.csv"
    with raises(ValueError) as err:
        extract_bucket_key(test_uri)
    assert str(err.value) == f"S3 URI must include bucket and key: {test_uri}"


def test_extract_bucket_key_raises_value_error_if_provided_no_key():
    test_uri = "s3://test_bucket"
    with raises(ValueError) as err:
        extract_bucket_key(test_uri)
    assert str(err.value) == f"S3 URI must include bucket and key: {test_uri}"

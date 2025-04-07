from src.gdpr_obfuscator import get_col_nums


def test_get_col_nums_returns_a_list():
    test_header = ["col1", "col2", "col3"]
    test_pii_fields = ["col2"]
    output = get_col_nums(test_header, test_pii_fields)
    assert isinstance(output, list)

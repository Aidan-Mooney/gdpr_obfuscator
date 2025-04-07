from src.gdpr_obfuscator import get_col_nums


def test_get_col_nums_returns_a_list():
    test_header = ["col1", "col2", "col3"]
    test_pii_fields = ["col2"]
    output = get_col_nums(test_header, test_pii_fields)
    assert isinstance(output, list)


def test_get_col_nums_returns_an_empty_list_when_pii_fields_is_empty():
    test_header = ["col1", "col2", "col3"]
    test_pii_fields = []
    output = get_col_nums(test_header, test_pii_fields)
    assert len(output) == 0


def test_get_col_nums_will_return_the_correct_index_for_one_pii_field():
    test_header = ["col1", "col2", "col3"]
    test_pii_fields = ["col2"]
    output = get_col_nums(test_header, test_pii_fields)
    assert len(output) == 1
    assert 1 in output


def test_get_col_nums_will_return_multiple_indexes_for_multiple_pii_fields():
    test_header = [
        "col1",
        "col2",
        "col3",
        "col4",
        "col5",
        "col6",
        "col7",
        "col8",
        "col9",
    ]
    test_pii_fields = ["col2", "col5", "col7"]
    output = get_col_nums(test_header, test_pii_fields)
    assert len(output) == 3
    assert 1 in output
    assert 4 in output
    assert 6 in output


def test_get_col_nums_will_return_all_indexes_if_a_pii_field_is_in_the_headers_list_multiple_times():
    test_header = [
        "col1",
        "col2",
        "col3",
        "col4",
        "col5",
        "col6",
        "col2",
        "col8",
        "col9",
    ]
    test_pii_fields = ["col2"]
    output = get_col_nums(test_header, test_pii_fields)
    assert len(output) == 2
    assert 1 in output
    assert 6 in output

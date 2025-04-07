from src.gdpr_obfuscator import csv_string_to_list


def test_csv_string_to_list_returns_a_list():
    test_line = "test1, test2, test3\n"
    output = csv_string_to_list(test_line)
    assert isinstance(output, list)

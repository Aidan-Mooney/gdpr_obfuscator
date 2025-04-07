from src.gdpr_obfuscator import csv_string_to_list


def test_csv_string_to_list_returns_a_list():
    test_line = "test1,test2,test3\n"
    output = csv_string_to_list(test_line)
    assert isinstance(output, list)


def test_csv_string_to_list_returns_a_list_of_length_one_when_input_has_no_commas():
    test_line = "test1\n"
    output = csv_string_to_list(test_line)
    assert len(output) == 1


def test_csv_string_to_list_removes_the_new_line_character():
    test_line = "test1,test2,test3\n"
    output = csv_string_to_list(test_line)
    assert output[-1][-1] != "\n"


def test_csv_string_to_list_separates_an_input_with_one_comma():
    test_line = "test1,test2\n"
    output = csv_string_to_list(test_line)
    assert output == ["test1", "test2"]


def test_csv_string_to_list_separates_an_input_with_multiple_commas():
    test_line = "test1,test2,test3,test4,test5\n"
    output = csv_string_to_list(test_line)
    assert output == ["test1", "test2", "test3", "test4", "test5"]

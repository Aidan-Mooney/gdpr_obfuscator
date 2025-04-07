from src.gdpr_obfuscator import list_to_csv_string


def test_list_to_csv_string_returns_a_str():
    test_list = ["test1", "test2", "test3"]
    output = list_to_csv_string(test_list)
    assert isinstance(output, str)


def test_empty_list_returns_a_new_line_character():
    test_list = []
    output = list_to_csv_string(test_list)
    assert output == "\n"


def test_list_of_length_one_returns_correct_output():
    test_list = ["item"]
    output = list_to_csv_string(test_list)
    assert output == "item\n"


def test_list_of_arbitrary_length_returns_correct_output():
    test_list = ["item1", "item2", "item3", "item4"]
    output = list_to_csv_string(test_list)
    assert output == "item1,item2,item3,item4\n"

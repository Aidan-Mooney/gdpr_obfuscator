from src.gdpr_obfuscator import edit_line


def test_edit_line_returns_a_str():
    test_line = "test1,test2,test3\n"
    test_nums = [1]
    output = edit_line(test_line, test_nums)
    assert isinstance(output, str)


def test_edit_line_with_empty_test_nums_is_unchanged():
    test_line = "test1,test2,test3\n"
    test_nums = []
    output = edit_line(test_line, test_nums)
    assert output == test_line


def test_edit_line_can_replace_one_word_with_asterisks():
    test_line = "test1,test2,test3\n"
    test_nums = [1]
    output = edit_line(test_line, test_nums)
    assert output == "test1,***,test3\n"


def test_edit_line_can_replace_multiple_words_with_asterisks():
    test_line = "test1,test2,test3,test4,test5\n"
    test_nums = [1, 3]
    output = edit_line(test_line, test_nums)
    assert output == "test1,***,test3,***,test5\n"

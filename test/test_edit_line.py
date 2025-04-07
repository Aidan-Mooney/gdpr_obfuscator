from src.gdpr_obfuscator import edit_line


def test_edit_line_returns_a_str():
    test_line = "test1, test2, test3\n"
    test_nums = [1]
    output = edit_line(test_line, test_nums)
    assert isinstance(output, str)

from src.gdpr_obfuscator import lambda_handler


def test_null():
    event = {}
    lambda_handler(event, None)
    assert True

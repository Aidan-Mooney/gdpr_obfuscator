from io import BytesIO
from src.gdpr_obfuscator import gdpr_obfuscator


def test_gdpr_obfuscator_returns_a_bytesio_object():
    event = {"file_to_obfuscate": "", "pii_fields": []}
    output = gdpr_obfuscator(event)
    assert isinstance(output, BytesIO)

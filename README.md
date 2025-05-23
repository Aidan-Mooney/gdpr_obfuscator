# GDPR Obfuscator

A Python library to anonymize Personally Identifiable Information (PII) in data files for GDPR compliance.

Currently supports:
- CSV files
- JSON files
- JSON Lines files

---

## Features

- Replace sensitive fields with obfuscated values (e.g., "***")
- Works with AWS S3 input/output (via boto3)
- Designed for integration in AWS pipelines (Lambda, Step Functions, Airflow)
- Compatible output for boto3.put_object

## Dependencies

- Python 3.8+
- make (required for running Makefile commands)
- boto3

## Installation

1. Clone the repository:

```bash
git clone <repo-url>
cd <repo-directory>
```

2. Create a virtual environment and install all dependencies:

```bash
make install-requirements
```

## Testing

To test the module is working correctly run:

```bash
make run-checks
```

During production I wrote tests to check the module obfuscates the file types in less than 60 seconds. If you would like to do this, for example, for a csv:

1. Add a 1MB CSV file to the `test-data` folder with the name `test_csv.csv`.

2. Now run:

```bash
TEST_TYPE=csv make run-checks
```

## Usage

### In Python:

```python
from gdpr_obfuscator import gdpr_obfuscator

event = {
    "file_to_obfuscate": "s3://my-bucket/path/to/file.csv",
    "pii_fields": ["name", "email_address"]
}

output_bytes = gdpr_obfuscator(event)
```
You can then upload output_bytes to S3 with boto3.put_object.

### In Command Line:

```bash
python -m gdpr_obfuscator --event config.json --output obfuscated.csv
```
This will save the obfuscated output to `obfuscated.csv` in the current directory.

## File Structure

```
gdpr-obfuscator/
├── requirements/
|   ├──requirements-dev-tools.txt
|   ├── requirements-external.txt
|   └── requirements-lambda.txt
├── src/
│   └── gdpr_obfuscator.py
├── test/
│   └── [multiple test files]
├── test-data/
|
├── LICENSE
├── Makefile
└── README.md
```

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

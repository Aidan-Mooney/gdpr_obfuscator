# GPDR Obfuscator

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

3. Test the module is working correctly:

```bash
make run-checks
```

## Usage

### In Python:

```python
from gdpr_obfuscator import obfuscate_csv

event = {
    "file_to_obfuscate": "s3://my-bucket/path/to/file.csv",
    "pii_fields": ["name", "email_address"]
}

output_bytes = obfuscate_csv(event)
```
You can then upload output_bytes to S3 with boto3.put_object.

### In Command Line:

```bash
python -m gdpr_obfuscator --event config.json --output obfuscated.csv
```
This will save the output bytes to a csv file.

## File Structure

```
gdpr-obfuscator/
├── src/
│   └── gdpr_obfuscator.py
├── test/
│   └── [multiple test files]
├── test-data/
│   ├── test_csv.csv
│   ├── test_json.json
│   └── test_jsonl.jsonl
├── requirements-external.txt
├── requirements-lambda.txt
├── requirements-dev-tools.txt
├── Makefile
└── README.md
```
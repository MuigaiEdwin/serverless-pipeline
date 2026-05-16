
import base64
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key


log_level = os.environ.get("LOG_LEVEL", "INFO")
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, log_level, logging.INFO))


dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ["DYNAMODB_TABLE"]
table = dynamodb.Table(TABLE_NAME)


# Masking helpers 

def mask_email(value: str) -> str:
    """
    jo**@example.com  →  jo**@***.com
    Keeps the first two characters of the local part visible.
    """
    if not value or "@" not in value:
        return value
    local, domain = value.split("@", 1)
    masked_local = local[:2] + "*" * max(len(local) - 2, 2)
    domain_parts = domain.split(".")
    masked_domain = "*" * len(domain_parts[0]) + "." + domain_parts[-1]
    return f"{masked_local}@{masked_domain}"


def mask_phone(value: str) -> str:
    """
    +254712345678  →  +254***5678
    Keeps country code prefix and last 4 digits.
    """
    digits = re.sub(r"\D", "", value)
    if len(digits) < 7:
        return "***"
    return digits[:3] + "*" * (len(digits) - 7) + digits[-4:]


def mask_ssn(value: str) -> str:
    """
    123-45-6789  →  ***-**-6789
    """
    clean = re.sub(r"\D", "", value)
    return f"***-**-{clean[-4:]}" if len(clean) >= 4 else "***-**-****"


def mask_name(value: str) -> str:
    """
    John Doe  →  J*** D**
    Preserves initials only.
    """
    parts = value.split()
    return " ".join(p[0] + "*" * (len(p) - 1) for p in parts)


# Map of field names → masking function
MASKING_RULES: dict = {
    "email":      mask_email,
    "phone":      mask_phone,
    "mobile":     mask_phone,
    "ssn":        mask_ssn,
    "national_id": mask_ssn,
    "full_name":  mask_name,
    "name":       mask_name,
}


def apply_masking(record: dict) -> dict:
    """
    Walk every key in the record and apply masking if the key
    matches a known PII field name. Returns a new dict.
    """
    masked = {}
    for key, value in record.items():
        lower_key = key.lower()
        if lower_key in MASKING_RULES and isinstance(value, str):
            masked[key] = MASKING_RULES[lower_key](value)
            logger.debug("Masked field: %s", key)
        else:
            masked[key] = value
    return masked


#  DynamoDB persistence 
def persist_record(record: dict, sequence_number: str) -> None:
    """
    Write a masked record to DynamoDB.
    Adds a generated record_id (UUID) and ingested_at timestamp.
    """
    item = {
        "record_id":       str(uuid.uuid4()),
        "ingested_at":     datetime.now(timezone.utc).isoformat(),
        "sequence_number": sequence_number,
        **record,
    }
    table.put_item(Item=item)
    logger.info("Persisted record_id=%s", item["record_id"])



def lambda_handler(event: dict, context) -> dict:
    """
    Entry point invoked by Kinesis event source mapping.

    Each event contains a batch of Kinesis records. We:
      1. Base64-decode and JSON-parse each record's data payload.
      2. Apply PII masking.
      3. Write the masked record to DynamoDB.
    """
    records = event.get("Records", [])
    logger.info("Received batch of %d records", len(records))

    success_count = 0
    failure_count = 0

    for kinesis_record in records:
        sequence_number = kinesis_record["kinesis"]["sequenceNumber"]
        try:
            # Decode Kinesis payload
            raw_bytes = base64.b64decode(kinesis_record["kinesis"]["data"])
            payload = json.loads(raw_bytes.decode("utf-8"))
            logger.debug("Decoded payload keys: %s", list(payload.keys()))

            # Mask PII
            masked_payload = apply_masking(payload)

            # Persist to DynamoDB
            persist_record(masked_payload, sequence_number)
            success_count += 1

        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON for sequence %s: %s", sequence_number, exc)
            failure_count += 1
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Failed to process sequence %s: %s", sequence_number, exc, exc_info=True
            )
            failure_count += 1

    logger.info(
        "Batch complete — success: %d, failed: %d", success_count, failure_count
    )

    return {
        "statusCode": 200,
        "body": {
            "processed": success_count,
            "failed":    failure_count,
        },
    }

#!/usr/bin/env python3
"""
Test producer — sends sample PII-containing records to the Kinesis stream.

Usage:
    python scripts/producer.py --stream serverless-pipeline-stream --count 5

Prerequisites:
    pip install boto3
    AWS credentials configured (aws configure OR environment variables)
"""

import argparse
import base64
import json
import random
import time
import uuid
from datetime import datetime, timezone

import boto3


SAMPLE_NAMES  = ["Alice Wanjiru", "Brian Otieno", "Carol Muthoni", "David Kimani"]
SAMPLE_EMAILS = ["alice@example.com", "brian@gmail.com", "carol@company.org"]
SAMPLE_PHONES = ["+254712345678", "+254723456789", "+254734567890"]
PRODUCTS      = ["laptop", "phone", "headphones", "monitor", "keyboard"]


def make_record() -> dict:
    """Generate a fake order record with PII fields."""
    return {
        "order_id":    str(uuid.uuid4()),
        "name":        random.choice(SAMPLE_NAMES),
        "email":       random.choice(SAMPLE_EMAILS),
        "phone":       random.choice(SAMPLE_PHONES),
        "product":     random.choice(PRODUCTS),
        "quantity":    random.randint(1, 5),
        "price_usd":   round(random.uniform(20.0, 800.0), 2),
        "created_at":  datetime.now(timezone.utc).isoformat(),
    }


def send_records(stream_name: str, count: int, region: str, delay: float) -> None:
    client = boto3.client("kinesis", region_name=region)

    print(f"Sending {count} record(s) to stream '{stream_name}' in {region}...\n")

    for i in range(1, count + 1):
        record = make_record()
        data   = json.dumps(record).encode("utf-8")

        response = client.put_record(
            StreamName=stream_name,
            Data=data,
            PartitionKey=record["order_id"],
        )

        print(f"[{i}/{count}] Sent order_id={record['order_id'][:8]}…  "
              f"shard={response['ShardId']}  "
              f"seq={response['SequenceNumber'][:20]}…")

        if delay and i < count:
            time.sleep(delay)

    print("\nDone. Check Lambda logs and DynamoDB to verify masking.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Kinesis test producer")
    parser.add_argument("--stream",  required=True,  help="Kinesis stream name")
    parser.add_argument("--count",   type=int, default=5, help="Number of records to send")
    parser.add_argument("--region",  default="us-east-1", help="AWS region")
    parser.add_argument("--delay",   type=float, default=0.5, help="Seconds between records")
    args = parser.parse_args()

    send_records(args.stream, args.count, args.region, args.delay)


if __name__ == "__main__":
    main()

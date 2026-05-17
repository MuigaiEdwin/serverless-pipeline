"""
Unit tests for PII masking functions in handler.py

Run with:
    python -m pytest tests/ -v
"""

import sys
import os
import pytest

# Allow importing handler without boto3 being configured
os.environ.setdefault("DYNAMODB_TABLE", "test-table")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

# Stub out boto3.resource so the module-level client init doesn't fail
import unittest.mock as mock
with mock.patch("boto3.resource"):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambda_src"))
    from handler import mask_email, mask_phone, mask_ssn, mask_name, apply_masking


class TestMaskEmail:
    def test_basic_email(self):
        result = mask_email("alice@example.com")
        assert result.startswith("al")
        assert "@" in result
        assert "alice" not in result

    def test_short_local_part(self):
        result = mask_email("ab@test.com")
        assert result.startswith("ab")

    def test_empty_string(self):
        assert mask_email("") == ""

    def test_no_at_symbol(self):
        assert mask_email("notanemail") == "notanemail"


class TestMaskPhone:
    def test_kenyan_number(self):
        result = mask_phone("+254712345678")
        assert result.endswith("5678")
        assert "712345" not in result

    def test_short_number(self):
        result = mask_phone("123")
        assert result == "***"


class TestMaskSSN:
    def test_standard_ssn(self):
        result = mask_ssn("123-45-6789")
        assert result == "***-**-6789"
        assert "123" not in result

    def test_no_dashes(self):
        result = mask_ssn("123456789")
        assert result.endswith("6789")


class TestMaskName:
    def test_full_name(self):
        result = mask_name("John Doe")
        assert result.startswith("J")
        assert "ohn" not in result

    def test_single_name(self):
        result = mask_name("Alice")
        assert result.startswith("A")
        assert len(result) > 1


class TestApplyMasking:
    def test_masks_known_fields(self):
        record = {
            "email": "test@example.com",
            "phone": "+254700000000",
            "product": "laptop",
            "price_usd": 299.99,
        }
        result = apply_masking(record)
        assert "test@example.com" not in result["email"]
        assert result["product"] == "laptop"
        assert result["price_usd"] == 299.99

    def test_preserves_non_pii(self):
        record = {"order_id": "abc-123", "quantity": 2}
        result = apply_masking(record)
        assert result["order_id"] == "abc-123"
        assert result["quantity"] == 2

    def test_non_string_pii_field_not_crashed(self):
        record = {"email": None, "phone": 12345}
        result = apply_masking(record)
        assert result["email"] is None

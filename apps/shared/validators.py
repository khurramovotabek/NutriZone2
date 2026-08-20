"""Reusable field validators shared across domains."""

import re

from django.core.exceptions import ValidationError

PHONE_REGEX = re.compile(r"^\+?[1-9]\d{6,14}$")


def validate_phone_number(value: str) -> None:
    """E.164-ish phone validation, used by accounts (OTP login) and orders
    (delivery contact) so both accept/reject the same shape of number."""
    if not PHONE_REGEX.match(value.replace(" ", "").replace("-", "")):
        raise ValidationError(
            "Enter a valid phone number, e.g. +998901234567.",
            code="invalid_phone_number",
        )


def validate_positive_amount(value) -> None:
    if value is None or value <= 0:
        raise ValidationError("Amount must be greater than zero.", code="invalid_amount")

"""Read-query helpers for accounts."""

from django.contrib.auth import get_user_model

User = get_user_model()


def find_by_username_or_email(identifier: str):
    return (
        User.objects.filter(username__iexact=identifier).first()
        or User.objects.filter(email__iexact=identifier).first()
    )

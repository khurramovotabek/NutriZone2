from django.contrib.auth import get_user_model

from apps.shared.exceptions import ServiceError

User = get_user_model()


class UserService:
    @staticmethod
    def change_password(user: User, old_password: str, new_password: str) -> None:
        if not user.check_password(old_password):
            raise ServiceError("Old password is incorrect.", code="invalid_password")
        user.set_password(new_password)
        user.save(update_fields=["password"])

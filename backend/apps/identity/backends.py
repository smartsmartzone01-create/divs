from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailOrPhoneBackend(ModelBackend):
    """Authenticate an account using a verified email or verified phone."""

    def authenticate(self, request, username=None, password=None, identifier=None, **kwargs):
        login_identifier = identifier or username or kwargs.get("email") or kwargs.get("phone_number")
        if not login_identifier or not password:
            return None

        Account = get_user_model()
        value = login_identifier.strip()
        try:
            if "@" in value:
                account = Account.objects.get(email__iexact=value)
                identifier_verified = account.email_verified
            else:
                account = Account.objects.get(phone_number=value)
                identifier_verified = account.phone_verified
        except (Account.DoesNotExist, Account.MultipleObjectsReturned):
            Account().set_password(password)
            return None

        if (
            identifier_verified
            and account.check_password(password)
            and self.user_can_authenticate(account)
        ):
            return account
        return None

from django.contrib.auth import authenticate


def authenticate_email_password(request, email, password):
    """Authenticate a password-backed account by email.

    Email addresses are normalized to lowercase to support any email provider.
    Verification delivery is deliberately separate from credential validation.
    """
    return authenticate(request=request, email=email.strip().lower(), password=password)

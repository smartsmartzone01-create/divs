from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.profiles.models import DriverProfile
from apps.verification.models import DriverVerification, DriverVerificationCheck


@receiver(post_save, sender=DriverProfile)
def create_driver_verification(sender, instance, created, **kwargs):
    """Start verification with every new driver profile, inside its creation flow."""
    if not created:
        return

    verification, _ = DriverVerification.objects.get_or_create(profile=instance)
    existing = set(verification.checks.values_list("check_type", flat=True))
    missing = [
        DriverVerificationCheck(verification=verification, check_type=check_type)
        for check_type, _label in DriverVerificationCheck.CheckType.choices
        if check_type not in existing
    ]
    if missing:
        DriverVerificationCheck.objects.bulk_create(missing)

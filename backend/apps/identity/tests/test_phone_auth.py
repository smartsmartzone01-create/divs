from django.test import TestCase, override_settings

from apps.identity.models import VerificationCode
from apps.identity.services.verification import (
    VerificationDeliveryNotConfigured,
    issue_verification_code,
    verify_code,
)


class FakeSMSProvider:
    deliveries = []

    def send_verification_code(self, phone_number, code, expires_in_seconds=600):
        self.deliveries.append(
            {
                "phone_number": phone_number,
                "code": code,
                "expires_in_seconds": expires_in_seconds,
            }
        )


class PhoneVerificationDeliveryTests(TestCase):
    def setUp(self):
        FakeSMSProvider.deliveries = []

    @override_settings(
        SMS_OTP_PROVIDER_CLASS="apps.identity.tests.test_phone_auth.FakeSMSProvider"
    )
    def test_phone_code_is_delivered_and_verified_by_divs(self):
        record = issue_verification_code(
            VerificationCode.Channel.PHONE,
            "+255712345678",
        )
        self.assertEqual(len(FakeSMSProvider.deliveries), 1)
        delivery = FakeSMSProvider.deliveries[0]
        self.assertEqual(delivery["phone_number"], "+255712345678")
        self.assertEqual(delivery["expires_in_seconds"], 600)
        self.assertNotEqual(record.code_hash, delivery["code"])
        self.assertTrue(
            verify_code(
                VerificationCode.Channel.PHONE,
                "+255712345678",
                delivery["code"],
            )
        )
        self.assertFalse(
            verify_code(
                VerificationCode.Channel.PHONE,
                "+255712345678",
                delivery["code"],
            )
        )

    @override_settings(SMS_OTP_PROVIDER_CLASS="")
    def test_phone_code_is_not_saved_when_provider_is_unconfigured(self):
        with self.assertRaises(VerificationDeliveryNotConfigured):
            issue_verification_code(
                VerificationCode.Channel.PHONE,
                "+255712345678",
            )
        self.assertFalse(
            VerificationCode.objects.filter(
                channel=VerificationCode.Channel.PHONE,
                target="+255712345678",
            ).exists()
        )

    @override_settings(
        SMS_OTP_PROVIDER_CLASS="apps.identity.tests.test_phone_auth.FakeSMSProvider"
    )
    def test_newly_delivered_code_invalidates_previous_code(self):
        issue_verification_code(
            VerificationCode.Channel.PHONE,
            "+255712345678",
        )
        old_code = FakeSMSProvider.deliveries[-1]["code"]
        issue_verification_code(
            VerificationCode.Channel.PHONE,
            "+255712345678",
        )
        new_code = FakeSMSProvider.deliveries[-1]["code"]

        self.assertFalse(
            verify_code(
                VerificationCode.Channel.PHONE,
                "+255712345678",
                old_code,
            )
        )
        self.assertTrue(
            verify_code(
                VerificationCode.Channel.PHONE,
                "+255712345678",
                new_code,
            )
        )

import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from PIL import Image

from apps.verification.storage import EvidenceStorageError, _read_and_validate


class EvidenceFileValidationTests(SimpleTestCase):
    def _jpeg(self):
        output = io.BytesIO()
        Image.new("RGB", (32, 32), color="white").save(output, format="JPEG")
        return output.getvalue()

    def test_accepts_real_jpeg_content_and_hashes_it(self):
        content = self._jpeg()
        uploaded = SimpleUploadedFile("identity.jpg", content, content_type="image/jpeg")

        validated, content_type, digest = _read_and_validate(uploaded)

        self.assertEqual(validated, content)
        self.assertEqual(content_type, "image/jpeg")
        self.assertEqual(len(digest), 64)

    def test_rejects_svg_even_when_named_as_jpeg(self):
        uploaded = SimpleUploadedFile(
            "identity.jpg",
            b"<svg xmlns='http://www.w3.org/2000/svg'></svg>",
            content_type="image/jpeg",
        )

        with self.assertRaises(EvidenceStorageError):
            _read_and_validate(uploaded)

    @override_settings(R2_MAX_UPLOAD_BYTES=5)
    def test_rejects_files_over_configured_size_limit(self):
        uploaded = SimpleUploadedFile("large.jpg", b"123456", content_type="image/jpeg")

        with self.assertRaises(EvidenceStorageError):
            _read_and_validate(uploaded)

    def test_rejects_malformed_pdf(self):
        uploaded = SimpleUploadedFile(
            "identity.pdf",
            b"%PDF-1.7\nthis is not a valid PDF",
            content_type="application/pdf",
        )

        with self.assertRaises(EvidenceStorageError):
            _read_and_validate(uploaded)

from rest_framework import serializers

from apps.operations.models import OperationsApplication


class OperationsApplicationReviewSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(
        choices=[
            (OperationsApplication.Status.APPROVED, "Approve"),
            (OperationsApplication.Status.REJECTED, "Reject"),
        ]
    )
    review_note = serializers.CharField(required=False, allow_blank=True, max_length=2000, trim_whitespace=True)

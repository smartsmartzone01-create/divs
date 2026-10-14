from rest_framework import serializers

from apps.performance.models import (
    AvailabilityRestriction,
    DriverScore,
    PerformanceAppeal,
    PerformanceEvent,
    PerformanceEventReview,
    PerformanceEventScoreApplication,
    PerformanceScoringRule,
    ScoreHistory,
)


class PerformanceEventSerializer(serializers.ModelSerializer):
    driver_id = serializers.UUIDField(write_only=True)
    driver = serializers.UUIDField(source="driver_id", read_only=True)

    class Meta:
        model = PerformanceEvent
        fields = [
            "id", "driver", "driver_id", "category", "event_code", "severity",
            "status", "title", "description", "occurred_at", "source_type",
            "source_reference", "evidence_references", "submitted_by",
            "reviewed_by", "reviewed_at", "decision_reason", "created_at",
        ]
        read_only_fields = [
            "id", "status", "submitted_by", "reviewed_by", "reviewed_at",
            "decision_reason", "created_at",
        ]

    def validate_category(self, value):
        if value == PerformanceEvent.Category.CORRECTION:
            raise serializers.ValidationError(
                "Correction events must use the audited appeal-correction workflow."
            )
        return value

    def validate_event_code(self, value):
        value = value.strip().lower()
        if not value or len(value) > 64:
            raise serializers.ValidationError("Provide a stable event code of 1–64 characters.")
        if any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-_." for char in value):
            raise serializers.ValidationError(
                "Use lowercase letters, numbers, hyphens, underscores, or dots."
            )
        return value

    def validate_evidence_references(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Evidence references must be a list.")
        return value


class PerformanceEventReviewSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=PerformanceEventReview.Decision.choices)
    reason = serializers.CharField()
    requested_evidence = serializers.CharField(required=False, allow_blank=True, default="")


class ScoringRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceScoringRule
        fields = [
            "id", "name", "category", "event_code", "severity", "points_delta",
            "status", "reason", "created_by", "approved_by", "approved_at",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "status", "created_by", "approved_by", "approved_at",
            "created_at", "updated_at",
        ]


class AppealCreateSerializer(serializers.Serializer):
    reason = serializers.CharField()
    evidence_references = serializers.ListField(
        child=serializers.CharField(max_length=500),
        required=False,
        default=list,
    )


class AppealDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(
        choices=[
            (PerformanceAppeal.Status.UPHELD, "Appeal successful"),
            (PerformanceAppeal.Status.DENIED, "Appeal unsuccessful"),
        ]
    )
    reason = serializers.CharField()


class ScoreOverrideSerializer(serializers.Serializer):
    new_score = serializers.IntegerField(min_value=0, max_value=100)
    reason = serializers.CharField()


class ScoreCorrectionSerializer(serializers.Serializer):
    reason = serializers.CharField()


class ScoreSummarySerializer(serializers.ModelSerializer):
    driver_id = serializers.UUIDField(read_only=True)
    effective_score = serializers.IntegerField(read_only=True)

    class Meta:
        model = DriverScore
        fields = [
            "id", "driver_id", "calculated_score", "manual_override_score",
            "effective_score", "manual_override_reason", "manual_override_at",
            "calculation_updated_at", "created_at", "updated_at",
        ]


class ScoreHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoreHistory
        fields = [
            "id", "event", "change_type", "previous_score", "new_score",
            "reason", "rule_reference", "actor", "created_at",
        ]


class AvailabilityRestrictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilityRestriction
        fields = [
            "id", "kind", "status", "reason", "source_event", "source_score",
            "created_by", "created_at", "released_by", "released_at",
            "release_reason",
        ]

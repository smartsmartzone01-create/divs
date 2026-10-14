from django.core.exceptions import PermissionDenied as DP, ValidationError as DV
from rest_framework import status
from rest_framework.response import Response
from rest_framework import serializers
from apps.performance.models import PerformanceAppeal
from apps.performance.services.appeals import submit_performance_appeal, decide_performance_appeal
from apps.performance.services.score_corrections import correct_score_after_upheld_appeal
from apps.performance.views.events import OperationsPerformanceAPIView, translate_error
from common.views import RoleProtectedAPIView

class AppealInput(serializers.Serializer):
    reason = serializers.CharField()
    evidence_references = serializers.ListField(child=serializers.CharField(max_length=500), required=False, default=list)

class AppealDecisionInput(serializers.Serializer):
    decision = serializers.ChoiceField(choices=[("upheld", "Upheld"), ("denied", "Denied")])
    reason = serializers.CharField()

class CorrectionInput(serializers.Serializer):
    reason = serializers.CharField()

class DriverAppealsView(RoleProtectedAPIView):
    required_profile_type = "driver"

    def get(self, request):
        qs = PerformanceAppeal.objects.filter(appellant=request.user).select_related("event")[:100]
        return Response([{"id": str(a.pk), "event_id": str(a.event_id), "reason": a.reason,
            "evidence_references": a.evidence_references, "status": a.status,
            "decision_reason": a.decision_reason, "correction_required": a.correction_required,
            "created_at": a.created_at, "decided_at": a.decided_at} for a in qs])

    def post(self, request, event_id):
        serializer = AppealInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            appeal = submit_performance_appeal(event_id=event_id, appellant=request.user, **serializer.validated_data)
        except (DP, DV) as exc:
            translate_error(exc)
        return Response({"id": str(appeal.pk), "event_id": str(appeal.event_id),
            "status": appeal.status, "created_at": appeal.created_at}, status=status.HTTP_201_CREATED)

class AppealReviewView(OperationsPerformanceAPIView):
    def post(self, request, appeal_id):
        serializer = AppealDecisionInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            appeal, decision = decide_performance_appeal(appeal_id=appeal_id, reviewer=request.user, **serializer.validated_data)
        except (DP, DV) as exc:
            translate_error(exc)
        return Response({"appeal_id": str(appeal.pk), "status": appeal.status,
            "correction_required": appeal.correction_required, "decision_id": str(decision.pk)})

class AppealCorrectionView(OperationsPerformanceAPIView):
    def post(self, request, appeal_id):
        serializer = CorrectionInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            correction = correct_score_after_upheld_appeal(appeal_id=appeal_id, actor=request.user, **serializer.validated_data)
        except (DP, DV) as exc:
            translate_error(exc)
        return Response({"id": str(correction.pk), "appeal_id": str(correction.appeal_id),
            "event_id": str(correction.event_id), "previous_calculated_score": correction.previous_calculated_score,
            "new_calculated_score": correction.new_calculated_score, "reason": correction.reason,
            "created_at": correction.created_at})

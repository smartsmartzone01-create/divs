from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied, ValidationError as DjangoValidationError
from apps.performance.models import PerformanceScoringRule
from apps.performance.serializers import ScoringRuleSerializer
from apps.performance.services.scoring_rules import propose_scoring_rule
from apps.performance.views.events import OperationsPerformanceAPIView, translate_error

class ScoringRuleListCreateView(OperationsPerformanceAPIView):
    def get(self, request):
        qs = PerformanceScoringRule.objects.all()[:200]
        return Response(ScoringRuleSerializer(qs, many=True).data)

    def post(self, request):
        serializer = ScoringRuleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            rule = propose_scoring_rule(actor=request.user, **serializer.validated_data)
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            translate_error(exc)
        return Response(ScoringRuleSerializer(rule).data, status=status.HTTP_201_CREATED)


from django.shortcuts import get_object_or_404
from apps.performance.models import DriverScore, ScoreHistory
from apps.performance.serializers import ScoreHistorySerializer, ScoreSummarySerializer
from apps.performance.services.score_overrides import override_driver_score
from apps.performance.services.scoring_rules import approve_scoring_rule, retire_scoring_rule


class ScoringRuleActionView(OperationsPerformanceAPIView):
    def post(self, request, rule_id, action):
        try:
            if action == "approve":
                rule = approve_scoring_rule(rule_id=rule_id, actor=request.user)
            elif action == "retire":
                rule = retire_scoring_rule(rule_id=rule_id, actor=request.user)
            else:
                return Response({"detail": "Unknown action."}, status=404)
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            translate_error(exc)
        return Response(ScoringRuleSerializer(rule).data)


class ScoreOverrideInput(serializers.Serializer):
    new_score = serializers.IntegerField(min_value=0, max_value=100)
    reason = serializers.CharField()


class ScoreOverrideView(OperationsPerformanceAPIView):
    def post(self, request, score_id):
        serializer = ScoreOverrideInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            score, history = override_driver_score(
                score_id=score_id, actor=request.user, **serializer.validated_data
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            translate_error(exc)
        return Response({"score": ScoreSummarySerializer(score).data, "history_id": str(history.pk)})


class ScoreHistoryListView(OperationsPerformanceAPIView):
    def get(self, request, score_id):
        score = get_object_or_404(DriverScore, pk=score_id)
        history = ScoreHistory.objects.filter(score=score).order_by("-created_at")[:200]
        return Response(ScoreHistorySerializer(history, many=True).data)

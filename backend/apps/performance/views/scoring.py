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

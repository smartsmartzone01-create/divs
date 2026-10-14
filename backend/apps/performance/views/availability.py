from django.core.exceptions import PermissionDenied as DP, ValidationError as DV
from rest_framework import serializers
from rest_framework.response import Response

from apps.performance.services.availability import (
    place_critical_incident_restriction,
    release_availability_restriction,
)
from apps.performance.views.events import OperationsPerformanceAPIView, translate_error


class RestrictionReasonInput(serializers.Serializer):
    reason = serializers.CharField()


class CriticalRestrictionView(OperationsPerformanceAPIView):
    def post(self, request, event_id):
        serializer = RestrictionReasonInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = place_critical_incident_restriction(
                event_id=event_id, actor=request.user, **serializer.validated_data
            )
        except (DP, DV) as exc:
            translate_error(exc)
        return Response({
            "id": str(item.pk), "driver_id": str(item.driver_id),
            "kind": item.kind, "status": item.status,
            "reason": item.reason, "created_at": item.created_at,
        })


class RestrictionReleaseView(OperationsPerformanceAPIView):
    def post(self, request, restriction_id):
        serializer = RestrictionReasonInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = release_availability_restriction(
                restriction_id=restriction_id, actor=request.user, **serializer.validated_data
            )
        except (DP, DV) as exc:
            translate_error(exc)
        return Response({
            "id": str(item.pk), "driver_id": str(item.driver_id),
            "kind": item.kind, "status": item.status,
            "released_at": item.released_at, "release_reason": item.release_reason,
        })

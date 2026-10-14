from django.core.exceptions import PermissionDenied as DjangoPermissionDenied, ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.operations.permissions import HasOperationsCapability
from apps.profiles.models import DriverProfile
from apps.performance.models import PerformanceEvent
from apps.performance.serializers import PerformanceEventReviewSerializer, PerformanceEventSerializer
from apps.performance.services.event_reviews import review_performance_event
from common.permissions import HasRequiredProfile
from common.views import RoleProtectedAPIView


def translate_error(exc):
    if isinstance(exc, DjangoPermissionDenied):
        raise PermissionDenied(str(exc))
    detail = getattr(exc, "message_dict", None) or getattr(exc, "messages", [str(exc)])
    raise ValidationError(detail)


class OperationsPerformanceAPIView(RoleProtectedAPIView):
    required_profile_type = "operations"
    required_operations_capability = "manage_driver_performance"
    permission_classes = [IsAuthenticated, HasRequiredProfile, HasOperationsCapability]


class PerformanceEventListCreateView(OperationsPerformanceAPIView):
    def get(self, request):
        queryset = PerformanceEvent.objects.select_related("driver").all()
        if request.query_params.get("driver_id"):
            queryset = queryset.filter(driver_id=request.query_params["driver_id"])
        if request.query_params.get("status"):
            queryset = queryset.filter(status=request.query_params["status"])
        return Response(PerformanceEventSerializer(queryset[:200], many=True).data)

    def post(self, request):
        serializer = PerformanceEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        driver_id = serializer.validated_data.pop("driver_id")
        driver = get_object_or_404(DriverProfile, pk=driver_id)
        event = serializer.save(
            driver=driver,
            submitted_by=request.user,
            source_type=PerformanceEvent.SourceType.OPERATIONS,
        )
        return Response(PerformanceEventSerializer(event).data, status=status.HTTP_201_CREATED)


class PerformanceEventReviewView(OperationsPerformanceAPIView):
    def post(self, request, event_id):
        serializer = PerformanceEventReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            event, review = review_performance_event(
                event_id=event_id,
                reviewer=request.user,
                **serializer.validated_data,
            )
        except (DjangoPermissionDenied, DjangoValidationError) as exc:
            translate_error(exc)
        return Response({
            "event_id": str(event.pk),
            "status": event.status,
            "review_id": str(review.pk),
            "reviewed_at": event.reviewed_at,
        })

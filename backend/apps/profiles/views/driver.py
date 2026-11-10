from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.operations.permissions import HasOperationsCapability
from apps.profiles.models import DriverProfile
from apps.profiles.serializers import AdminDriverDirectorySerializer, DriverProfileSerializer
from common.views import RoleProtectedAPIView
from rest_framework.views import APIView


class DriverProfileView(RoleProtectedAPIView):
    """Return the signed-in driver's own profile and registration information."""

    required_profile_type = "driver"

    def get(self, request):
        profile = get_object_or_404(
            DriverProfile.objects.select_related("registration", "registration__account"),
            registration__account=request.user,
        )
        return Response(DriverProfileSerializer(profile).data)


class OperationsDriverDirectoryView(APIView):
    """Search all registered driver profiles for authorized operations staff."""

    permission_classes = [IsAuthenticated, HasOperationsCapability]
    required_operations_capability = "manage_driver_registrations"
    page_size = 50

    def get(self, request):
        queryset = DriverProfile.objects.select_related(
            "registration", "registration__account", "verification"
        ).all()

        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(registration__first_name__icontains=search)
                | Q(registration__middle_name__icontains=search)
                | Q(registration__last_name__icontains=search)
                | Q(registration__account__email__icontains=search)
                | Q(registration__account__phone_number__icontains=search)
                | Q(registration__region__icontains=search)
                | Q(registration__district__icontains=search)
                | Q(registration__residential_area__icontains=search)
            )

        profile_status = request.query_params.get("profile_status", "").strip()
        if profile_status:
            valid_statuses = {value for value, _label in DriverProfile.Status.choices}
            if profile_status not in valid_statuses:
                return Response({"detail": "Invalid driver status filter."}, status=400)
            queryset = queryset.filter(status=profile_status)

        verification_status = request.query_params.get("verification_status", "").strip()
        if verification_status:
            valid_verification_statuses = {"pending", "in_review", "approved", "rejected", "not_started"}
            if verification_status not in valid_verification_statuses:
                return Response({"detail": "Invalid verification status filter."}, status=400)
            if verification_status == "not_started":
                queryset = queryset.filter(verification__isnull=True)
            else:
                queryset = queryset.filter(verification__status=verification_status)

        paginator = Paginator(queryset.order_by("-created_at"), self.page_size)
        try:
            page = paginator.page(request.query_params.get("page", 1))
        except (PageNotAnInteger, EmptyPage):
            page = paginator.page(1)

        return Response({
            "count": paginator.count,
            "page": page.number,
            "page_size": self.page_size,
            "total_pages": paginator.num_pages,
            "results": AdminDriverDirectorySerializer(page.object_list, many=True).data,
        })

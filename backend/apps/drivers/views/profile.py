from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.drivers.models import DriverProfile
from apps.drivers.serializers import DriverProfileSerializer


class DriverProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(DriverProfile, account=request.user)
        return Response(DriverProfileSerializer(profile).data)

    def post(self, request):
        if DriverProfile.objects.filter(account=request.user).exists():
            return Response(
                {"detail": "A driver profile already exists for this account."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = DriverProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                profile = serializer.save(account=request.user)
        except IntegrityError:
            return Response(
                {"detail": "A driver profile already exists for this account."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            DriverProfileSerializer(profile).data,
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request):
        profile = get_object_or_404(DriverProfile, account=request.user)
        serializer = DriverProfileSerializer(
            profile,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(DriverProfileSerializer(profile).data)

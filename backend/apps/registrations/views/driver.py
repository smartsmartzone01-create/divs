from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.registrations.models import DriverRegistration
from apps.registrations.serializers import DriverRegistrationSerializer


class DriverRegistrationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        registration = get_object_or_404(DriverRegistration, account=request.user)
        return Response(DriverRegistrationSerializer(registration).data)

    def post(self, request):
        if DriverRegistration.objects.filter(account=request.user).exists():
            return Response(
                {"detail": "A driver registration already exists for this account."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = DriverRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                registration = serializer.save(account=request.user)
        except IntegrityError:
            return Response(
                {"detail": "A driver registration already exists for this account."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(DriverRegistrationSerializer(registration).data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        registration = get_object_or_404(DriverRegistration, account=request.user)
        serializer = DriverRegistrationSerializer(registration, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        registration = serializer.save()
        return Response(DriverRegistrationSerializer(registration).data)

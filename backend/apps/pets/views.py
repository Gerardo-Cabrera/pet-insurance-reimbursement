from django.db.models import ProtectedError
from django.db.models import Count
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.users.models import User

from .models import Pet
from .permissions import PetPermission
from .serializers import PetSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Pets"],
        summary="List pets",
        description=(
            "Customers only see their own pets. Support and admin users can review all pets."
        ),
    ),
    retrieve=extend_schema(
        tags=["Pets"],
        summary="Retrieve a pet",
    ),
    create=extend_schema(
        tags=["Pets"],
        summary="Create a pet",
        description=(
            "Register a new insured pet. `coverage_end` is calculated automatically as "
            "`coverage_start + 365 days`."
        ),
        responses={
            201: PetSerializer,
            403: OpenApiResponse(description="Only customers and admins can create pets."),
        },
        examples=[
            OpenApiExample(
                "Create pet request",
                value={
                    "name": "Milo",
                    "species": "DOG",
                    "birth_date": "2020-01-01",
                    "coverage_start": "2026-01-01",
                },
                request_only=True,
            )
        ],
    ),
    update=extend_schema(
        tags=["Pets"],
        summary="Replace a pet",
    ),
    partial_update=extend_schema(
        tags=["Pets"],
        summary="Partially update a pet",
    ),
    destroy=extend_schema(
        tags=["Pets"],
        summary="Delete a pet",
        description=(
            "A pet can only be deleted when it has no associated claim history."
        ),
        responses={
            204: OpenApiResponse(description="Pet deleted."),
            400: OpenApiResponse(
                description="The pet has claims history and cannot be deleted."
            ),
        },
    ),
)
class PetViewSet(viewsets.ModelViewSet):
    queryset = Pet.objects.none()
    serializer_class = PetSerializer
    permission_classes = [PetPermission]
    search_fields = ("name", "species", "owner__email")
    ordering_fields = ("created_at", "coverage_start", "name")

    def get_queryset(self):
        queryset = (
            Pet.objects.select_related("owner")
            .annotate(claim_count=Count("claims"))
            .order_by("-created_at")
        )
        if getattr(self, "swagger_fake_view", False):
            return queryset.none()

        user = getattr(self.request, "user", None)
        if not user or not user.is_authenticated:
            return queryset.none()

        if user.role in {User.Role.ADMIN, User.Role.SUPPORT}:
            return queryset
        return queryset.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except ProtectedError:
            return Response(
                {
                    "detail": (
                        "This pet cannot be deleted because it already has claims history."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
